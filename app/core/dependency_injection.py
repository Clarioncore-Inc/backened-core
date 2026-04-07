from app.general.service import GeneralService
from app.accounts.services import AccountService
from app.courses.services import CourseService
from app.enrollments.services import EnrollmentService
from app.payments.services import PaymentService
from app.psychologist.services import PsychologistService
from app.reviews.services import ReviewService
from app.progress.services import ProgressService
from app.admin_panel.services import AdminService
from app.lessons.services import LessonService
from app.core.services import CoreService
from app.core.s3client import S3Service


class SERVICE_NAMES:
    GeneralService = "general_service"
    AccountService = "account_service"
    CourseService = "course_service"
    EnrollmentService = "enrollment_service"
    PaymentService = "payment_service"
    PsychologistService = "psychologist_service"
    ReviewService = "review_service"
    ProgressService = "progress_service"
    AdminService = "admin_service"
    LessonService = "lesson_service"
    CoreService = "core_service"
    S3Service = "s3_service"


class ServiceLocator:
    general_service: GeneralService
    account_service: AccountService
    course_service: CourseService
    enrollment_service: EnrollmentService
    payment_service: PaymentService
    psychologist_service: PsychologistService
    review_service: ReviewService
    progress_service: ProgressService
    admin_service: AdminService
    lesson_service: LessonService
    core_service: CoreService
    s3_service: S3Service

    def __init__(self):
        self._services = {}

    def register(self, name, service):
        self._services[name] = service

    def get(self, name):
        return self._services[name]

    def __getitem__(self, name):
        return self.get(name)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self.get(name)


service_locator = ServiceLocator()
service_locator.register(SERVICE_NAMES.GeneralService, GeneralService())
service_locator.register(SERVICE_NAMES.AccountService, AccountService())
service_locator.register(SERVICE_NAMES.CourseService, CourseService())
service_locator.register(SERVICE_NAMES.EnrollmentService, EnrollmentService())
service_locator.register(SERVICE_NAMES.PaymentService, PaymentService())
service_locator.register(
    SERVICE_NAMES.PsychologistService, PsychologistService())
service_locator.register(SERVICE_NAMES.ReviewService, ReviewService())
service_locator.register(SERVICE_NAMES.ProgressService, ProgressService())
service_locator.register(SERVICE_NAMES.AdminService, AdminService())
service_locator.register(SERVICE_NAMES.LessonService, LessonService())
service_locator.register(SERVICE_NAMES.CoreService, CoreService())
service_locator.register(SERVICE_NAMES.S3Service, S3Service())
