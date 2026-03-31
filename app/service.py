from app.models import Recruiter, Job, SessionLocal
from sqlalchemy.exc import IntegrityError

def save_recruiters(recruiters_list, company):
    """Save recruiters to database.

    Skips duplicates based on the unique email constraint.
    """
    db = SessionLocal()
    inserted = 0
    skipped = 0

    try:
        for recruiter in recruiters_list:
            email = recruiter.get("email")
            if not email:
                skipped += 1
                continue

            db_recruiter = Recruiter(
                name=recruiter.get("name"),
                email=email,
                company=company,
                title=recruiter.get("title"),
            )

            db.add(db_recruiter)

            # Force INSERT now so we can catch unique violations per row.
            try:
                db.flush()
                inserted += 1
            except IntegrityError:
                db.rollback()  # rollback the failed INSERT
                skipped += 1

        db.commit()
        print(f"✅ Saved {inserted} recruiter(s) to database (skipped {skipped} duplicates/invalid)")

    except Exception as e:
        db.rollback()
        print(f"❌ Error saving recruiters: {e}")

    finally:
        db.close()

def save_jobs(jobs_list, company):
    """Save jobs to database"""
    db = SessionLocal()
    try:
        for job in jobs_list:
            db_job = Job(
                title=job.get("title"),
                link=job.get("link"),
                company=company
            )
            db.add(db_job)
        
        db.commit()
        print(f"✅ Saved {len(jobs_list)} jobs to database")
    except Exception as e:
        db.rollback()
        print(f"❌ Error saving jobs: {e}")
    finally:
        db.close()

def get_all_recruiters():
    """Retrieve all recruiters from database"""
    db = SessionLocal()
    recruiters = db.query(Recruiter).all()
    db.close()
    return recruiters

def get_all_jobs():
    """Retrieve all jobs from database"""
    db = SessionLocal()
    jobs = db.query(Job).all()
    db.close()
    return jobs