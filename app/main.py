from app.hunter_service.recruiter_finder import extract_recruiter_emails
from app.service import save_recruiters, get_all_recruiters
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Find recruiter emails for a company domain (Hunter.io) and store them in Postgres."
    )
    parser.add_argument(
        "domain_or_url",
        help="Company domain or URL (e.g. stripe.com or https://stripe.com)"
    )
    parser.add_argument(
        "--company",
        "-c",
        default=None,
        help="Company name to store in DB (defaults to the domain)"
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=None,
        help="Optional max recruiters to save/display (does not change Hunter API limit)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write results to the database (print only)"
    )
    parser.add_argument(
        "--save-all",
        action="store_true",
        help="Save all discovered emails to DB (even if not recruiter/HR/manager), but keep filtering for sending"
    )

    # Email options
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send a crafted email to the collected addresses (requires SENDGRID_API_KEY)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not send emails; print what would be sent"
    )
    parser.add_argument(
        "--from-email",
        default=None,
        help="Verified SendGrid sender email address"
    )
    parser.add_argument(
        "--subject",
        default=None,
        help="Email subject override"
    )
    parser.add_argument(
        "--body",
        default=None,
        help="Email body override (plain text). You can use {name}, {company}, {title}, {email}."
    )
    parser.add_argument(
        "--test-to",
        default=None,
        help="Send exactly one test email to this address (overrides collected recipients)"
    )
    parser.add_argument(
        "--send-from-db",
        action="store_true",
        help="Send emails to recipients loaded from the database instead of the current scrape results"
    )
    parser.add_argument(
        "--db-company",
        default=None,
        help="When using --send-from-db, only send to recruiters where company matches this value"
    )
    parser.add_argument(
        "--db-title-contains",
        default=None,
        help="When using --send-from-db, only send to rows whose title contains this substring (case-insensitive), e.g. 'recruiter'"
    )
    parser.add_argument(
        "--db-use-title-filter",
        action="store_true",
        help="When using --send-from-db, apply the same title keyword filter preset (TITLE_FILTER_PRESET) used in scraping"
    )

    # H1B gating
    parser.add_argument(
        "--require-h1b",
        action="store_true",
        help="Only send emails if the company is known to sponsor H1B (cache->web lookup)"
    )
    parser.add_argument(
        "--h1b-company",
        default=None,
        help="Company name to use for H1B lookup (defaults to --company/domain_or_url)"
    )
    return parser.parse_args()


def _render(template: str, recruiter: dict, company: str) -> str:
    return template.format(
        name=recruiter.get("name") or "there",
        company=company,
        title=recruiter.get("title") or "",
        email=recruiter.get("email") or "",
    )


def main():
    args = parse_args()

    print("🚀 Starting Email Automation Pipeline...\n")

    domain_or_url = args.domain_or_url
    company = args.company or domain_or_url

    # Extract recruiter emails (filtered list)
    print(f"🔍 Finding recruiters for {domain_or_url}...")
    recruiters = extract_recruiter_emails(domain_or_url)

    # Optionally also extract all contacts for saving
    all_contacts = None
    if args.save_all and not args.no_save:
        from app.hunter_service.recruiter_finder import extract_all_emails
        all_contacts = extract_all_emails(domain_or_url)

    if args.limit is not None:
        recruiters = recruiters[: max(args.limit, 0)]

    print(f"Found {len(recruiters)} recruiters\n")

    # Save to database
    if args.no_save:
        print("⚠️  Skipping database save (--no-save set)")
    else:
        print("💾 Saving to database...")
        to_save = all_contacts if all_contacts is not None else recruiters
        if to_save:
            save_recruiters(to_save, company)

    # Optional: send email to collected addresses
    if args.send:
        from app.email_engine.sender import send_email_raw
        from app.models import SessionLocal, Recruiter

        # H1B gate (cache-first: DB -> file -> web)
        if args.require_h1b:
            from app.H1B_Collector.lookup import lookup_h1b_sponsorship

            h1b_company = args.h1b_company or company
            is_sponsor, source = lookup_h1b_sponsorship(h1b_company)
            if is_sponsor is not True:
                print(
                    f"🛑 H1B gate: '{h1b_company}' not confirmed as sponsor (result={is_sponsor}, source={source}). "
                    "Skipping send."
                )
                return
            print(f"✅ H1B gate: '{h1b_company}' confirmed sponsor (source={source}).")

        default_subject = f"Quick question about roles at {company}"
        default_body = (
            "Hi {name},\n\n"
            "I came across your contact while looking into opportunities at {company}. "
            "If you're the right person to speak with about engineering/infra roles, I'd love to connect. "
            "If not, could you point me to the appropriate recruiter or hiring manager?\n\n"
            "Thanks,\n"
            "<Your Name>\n"
        )

        subject_t = args.subject or default_subject
        body_t = args.body or default_body

        if not args.from_email and not args.dry_run:
            raise SystemExit("--from-email is required unless --dry-run is set")

        # Choose recipients
        if args.send_from_db:
            db = SessionLocal()
            try:
                q = db.query(Recruiter)
                if args.db_company:
                    q = q.filter(Recruiter.company == args.db_company)
                if args.db_title_contains:
                    # Case-insensitive contains
                    q = q.filter(Recruiter.title.ilike(f"%{args.db_title_contains}%"))

                db_rows = q.order_by(Recruiter.created_at.desc()).all()
                recipients = [
                    {"name": r.name, "email": r.email, "title": r.title}
                    for r in db_rows
                ]
            finally:
                db.close()

            if args.db_use_title_filter:
                # Apply the same filtering logic as the scrape pipeline.
                import os

                preset = (os.getenv("TITLE_FILTER_PRESET") or "recruiter_hr_managers").strip().lower()
                include_presets = {
                    "recruiter_only": [
                        "recruit", "sourc", "talent acquisition", "talent", "staffing",
                    ],
                    "recruiter_hr": [
                        "recruit", "sourc", "talent acquisition", "talent", "staffing",
                        "human resources", "hr", "people operations", "people ops", "people partner",
                    ],
                    "recruiter_hr_managers": [
                        "recruit", "sourc", "talent acquisition", "talent", "staffing",
                        "human resources", "hr", "people operations", "people ops", "people partner",
                        "hiring manager",
                        "engineering manager",
                        "software engineering manager",
                        "technical manager",
                        "tech lead",
                        "team lead",
                        "head of engineering",
                        "director of engineering",
                        "vp engineering",
                        "cto",
                        "platform",
                        "infrastructure",
                        "site reliability",
                        "sre",
                        "devops",
                    ],
                }

                include_keywords = [k.lower() for k in include_presets.get(preset, include_presets["recruiter_hr_managers"])]

                filtered = []
                for r in recipients:
                    title_l = (r.get("title") or "").lower()
                    if not title_l or title_l == "unknown":
                        continue
                    if any(k in title_l for k in include_keywords):
                        filtered.append(r)
                recipients = filtered
        else:
            recipients = recruiters

        if args.limit is not None:
            recipients = recipients[: max(args.limit, 0)]

        # If --test-to is provided, send exactly one email to that address.
        if args.test_to:
            test_recruiter = {
                "name": "Test Recipient",
                "email": args.test_to,
                "title": "",
            }

            subject = _render(subject_t, test_recruiter, company)
            body = _render(body_t, test_recruiter, company)

            if args.dry_run:
                print(f"--- Would send TEST email to: {args.test_to} ---")
                print(f"From: {args.from_email}")
                print(f"Subject: {subject}")
                print(body)
                print("---")
            else:
                confirm = input(
                    f"About to send 1 TEST email to {args.test_to}. Type 'yes' to continue: "
                ).strip().lower()
                if confirm != "yes":
                    print("Cancelled.")
                    return

                send_email_raw(
                    from_email=args.from_email,
                    to_email=args.test_to,
                    subject=subject,
                    body=body,
                )
        else:
            print("\n✉️  Email send enabled")
            if args.send_from_db:
                scope = f"DB ({'company=' + args.db_company if args.db_company else 'all companies'})"
                print(f"Recipients source: {scope}")
            else:
                print("Recipients source: current scrape")

            if args.dry_run:
                print("DRY RUN: no emails will be sent.\n")
            else:
                confirm = input(
                    f"About to send {len(recipients)} email(s) via SendGrid. Type 'yes' to continue: "
                ).strip().lower()
                if confirm != "yes":
                    print("Cancelled.")
                    return

            for r in recipients:
                to_email = r.get("email")
                if not to_email:
                    continue

                subject = _render(subject_t, r, company)
                body = _render(body_t, r, company)

                if args.dry_run:
                    print(f"--- Would send to: {to_email} ---")
                    print(f"Subject: {subject}")
                    print(body)
                    print("---")
                else:
                    send_email_raw(
                        from_email=args.from_email,
                        to_email=to_email,
                        subject=subject,
                        body=body,
                    )

    # Retrieve and display
    print("\n📊 Database Summary:")
    all_recruiters = get_all_recruiters() if not args.no_save else []
    print(f"Total Recruiters: {len(all_recruiters) if all_recruiters else 0}")

    # Display sample recruiters (from current run first; DB only if saved)
    to_display = recruiters if recruiters else all_recruiters
    if to_display:
        print("\nRecent Recruiters:")
        for recruiter in to_display[:5]:
            # recruiter can be dicts (current run) or ORM objects (DB)
            name = recruiter.get("name") if isinstance(recruiter, dict) else recruiter.name
            email = recruiter.get("email") if isinstance(recruiter, dict) else recruiter.email
            title = recruiter.get("title") if isinstance(recruiter, dict) else recruiter.title
            print(f"  - {name} ({email}) - {title}")


if __name__ == "__main__":
    main()