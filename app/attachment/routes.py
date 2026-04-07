from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.attachment.models import Attachment
from app.attachment.schemas import AttachmentResponse, AttachmentUpdate
from app.attachment.schemas import AttachmentStartRequest, AttachmentStartResponse, AttachmentFinishRequest
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User

router = APIRouter(prefix="/storages", tags=["storage"])


@cbv(router)
class AttachmentsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @router.post("/start", response_model=AttachmentStartResponse, status_code=201)
    def start_upload(self, payload: AttachmentStartRequest):
        import uuid
        s3_key = f"{uuid.uuid4()}/{payload.filename or 'file'}"
        use_put = payload.create_type == AttachmentStartRequest.CreateType.PUT
        if use_put:
            upload_url = service_locator.s3_service.generate_presigned_put(
                file_path=s3_key, file_type=payload.file_type
            )
            fields = None
        else:
            presigned = service_locator.s3_service.generate_presigned_post(
                file_path=s3_key, file_type=payload.file_type
            )
            upload_url = presigned["url"]
            fields = presigned["fields"]
        url = service_locator.s3_service.get_file_url(s3_key) or ""
        attachment = service_locator.general_service.create(
            db=self.db,
            data={
                "created_by": self.current_user.id,
                "s3_key": s3_key,
                "url": url,
                "filename": payload.filename,
                "mime_type": payload.mime_type or payload.file_type,
            },
            model=Attachment,
        )
        return AttachmentStartResponse(id=attachment.id, url=upload_url, fields=fields)

    @router.post("/{id}/finish", response_model=AttachmentResponse)
    def finish_upload(self, id: UUID, payload: AttachmentFinishRequest):
        from datetime import date
        attachment = service_locator.general_service.get(
            db=self.db, key=id, model=Attachment)
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        data = payload.model_dump(exclude_unset=True)
        data["upload_finished_at"] = date.today()
        data["file_size"] = service_locator.s3_service.get_file_size(
            attachment.s3_key) or None
        return service_locator.general_service.update_data(
            db=self.db, key=id, data=data, model=Attachment
        )

    @router.get("/{id}", response_model=AttachmentResponse)
    def get_attachment(self, id: UUID):
        attachment = service_locator.general_service.get(
            db=self.db, key=id, model=Attachment)
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        return attachment

    @router.put("/{id}", response_model=AttachmentResponse)
    def update_attachment(self, id: UUID, payload: AttachmentUpdate):
        attachment = service_locator.general_service.update_data(
            db=self.db, key=id, data=payload.model_dump(exclude_unset=True), model=Attachment
        )
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        return attachment

    @router.delete("/{id}", status_code=204)
    def delete_attachment(self, id: UUID):
        attachment = service_locator.general_service.get(
            db=self.db, key=id, model=Attachment)
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        if attachment.s3_key:
            service_locator.s3_service.delete_file(attachment.s3_key)
        service_locator.general_service.delete(
            db=self.db, key=id, model=Attachment)
