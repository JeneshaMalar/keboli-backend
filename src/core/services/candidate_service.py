import csv
import io
import uuid
from typing import List, Optional
from fastapi import HTTPException, status, UploadFile
from src.data.repositories.candidate_repo import CandidateRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.candidate_schema import CandidateCreate

class CandidateService:
    """
    Service layer for managing candidate data, including single creation, 
    bulk uploads, and organization-specific retrieval.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CandidateRepository(session)

    async def create_candidate(self, org_id: uuid.UUID, data: CandidateCreate):
        """
        Create a single candidate within an organization.
        
        Args:
            org_id: Unique identifier of the organization
            data: Pydantic model containing candidate details (email, name, etc.)
            
        Raises:
            HTTPException: If a candidate with the same email already exists in the org
            
        Returns:
            The newly created candidate object
        """
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
        """
        Retrieve all candidates belonging to a specific organization.
        
        Args:
            org_id: Unique identifier of the organization
            
        Raises:
            None
            
        Returns:
            A list of candidate objects
        """
        return await self.repo.get_multi_by_org(org_id)

    async def delete_candidate(self, org_id: uuid.UUID, candidate_id: uuid.UUID):
        """
        Remove a candidate from the system.
        
        Args:
            org_id: Organization ID to ensure the user has permission to delete
            candidate_id: Unique identifier of the candidate to remove
            
        Raises:
            HTTPException: If the candidate is not found or doesn't belong to the org
            
        Returns:
            A success message dictionary
        """
        candidate = await self.repo.get_by_id(candidate_id)
        if not candidate or candidate.org_id != org_id:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        await self.repo.delete(candidate_id)
        await self.session.commit()
        return {"message": "Candidate deleted successfully"}

    async def bulk_upload_candidates(self, org_id: uuid.UUID, file: UploadFile):
        """
        Process a CSV file to create multiple candidates at once.
        
        Args:
            org_id: Unique identifier of the organization
            file: The uploaded CSV file containing 'email' and 'name' columns
            
        Raises:
            HTTPException: If file format is invalid or if processing fails
            
        Returns:
            A dictionary containing the count of created records and a list of errors
        """
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported for bulk upload")
        
        try:
            content = await file.read()
            decoded = content.decode('utf-8-sig')
            f = io.StringIO(decoded)
            reader = csv.DictReader(f)
            
            candidates_to_create = []
            errors = []
            
            for row_num, row in enumerate(reader, 1):
                row_data = {k.lower().strip(): v for k, v in row.items() if k}
                
                email = row_data.get('email')
                name = row_data.get('name') or row_data.get('full name')
                
                if not email or not name:
                    if not any(row_data.values()): continue 
                    errors.append(f"Row {row_num}: Missing email or name. (Fields found: {list(row_data.keys())})")
                    continue
                
                email = email.strip()
                name = name.strip()
                
                existing = await self.repo.get_by_email_and_org(email, org_id)
                if existing:
                    errors.append(f"Row {row_num}: Candidate with email {email} already exists")
                    continue
                
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
