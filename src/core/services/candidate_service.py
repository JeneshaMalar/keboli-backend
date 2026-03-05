import csv
import io
import uuid
from typing import List, Optional
from fastapi import HTTPException, status, UploadFile
from src.data.repositories.candidate_repo import CandidateRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.candidate_schema import CandidateCreate

class CandidateService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CandidateRepository(session)

    async def create_candidate(self, org_id: uuid.UUID, data: CandidateCreate):
        existing = await self.repo.get_by_email_and_org(data.email, org_id)
        if existing:
            raise HTTPException(status_code=400, detail="Candidate with this email already exists in your organization")
        
        candidate_data = data.model_dump()
        candidate_data["org_id"] = org_id
        
        candidate = await self.repo.create(candidate_data)
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def get_org_candidates(self, org_id: uuid.UUID):
        return await self.repo.get_multi_by_org(org_id)

    async def delete_candidate(self, org_id: uuid.UUID, candidate_id: uuid.UUID):
        candidate = await self.repo.get_by_id(candidate_id)
        if not candidate or candidate.org_id != org_id:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        await self.repo.delete(candidate_id)
        await self.session.commit()
        return {"message": "Candidate deleted successfully"}

    async def bulk_upload_candidates(self, org_id: uuid.UUID, file: UploadFile):
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported for bulk upload")
        
        try:
            content = await file.read()
            # Handle potential BOM (Byte Order Mark) from some CSV editors
            decoded = content.decode('utf-8-sig')
            f = io.StringIO(decoded)
            reader = csv.DictReader(f)
            
            candidates_to_create = []
            errors = []
            
            for row_num, row in enumerate(reader, 1):
                # Make header lookups case-insensitive
                row_data = {k.lower().strip(): v for k, v in row.items() if k}
                
                email = row_data.get('email')
                name = row_data.get('name') or row_data.get('full name')
                
                if not email or not name:
                    if not any(row_data.values()): continue # Skip empty rows
                    errors.append(f"Row {row_num}: Missing email or name. (Fields found: {list(row_data.keys())})")
                    continue
                
                email = email.strip()
                name = name.strip()
                
                # Check for duplicate in the same organization
                existing = await self.repo.get_by_email_and_org(email, org_id)
                if existing:
                    errors.append(f"Row {row_num}: Candidate with email {email} already exists")
                    continue
                
                # Check for duplicates in the current list being processed
                if any(c["email"] == email for c in candidates_to_create):
                    errors.append(f"Row {row_num}: Duplicate email {email} found in CSV file")
                    continue

                candidates_to_create.append({
                    "email": email,
                    "name": name,
                    "org_id": org_id,
                })
                
            if candidates_to_create:
                created = await self.repo.create_bulk(candidates_to_create)
                await self.session.commit()
                return {"created_count": len(created), "errors": errors}
            else:
                return {"created_count": 0, "errors": errors}
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")
        finally:
            await file.close()
