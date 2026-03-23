"""
sqladmin – Admin UI for CerebroLearn
Mount point: /admin
Login credentials: set ADMIN_USERNAME / ADMIN_PASSWORD in .env
"""
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqladmin.filters import BooleanFilter, AllUniqueStringValuesFilter

from app.database import engine
from app.settings import ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_SECRET_KEY

# ── Domain model imports ───────────────────────────────────────────────────────
from app.accounts.models import User
from app.courses.models import Course
from app.lessons.models import Lesson
from app.enrollments.models import Enrollment
from app.progress.models import LessonProgress
from app.payments.models import Payment, Payout
from app.reviews.models import Review
from app.psychologist.models import PsychologistProfile, Booking


# ── Authentication backend ─────────────────────────────────────────────────────
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username", "")
        password = form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session.update({"admin_authenticated": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request):
        if not request.session.get("admin_authenticated"):
            return RedirectResponse(request.url_for("admin:login"), status_code=302)
        return True  # ← must be explicit; None is falsy and causes a redirect loop


# ── Model views ────────────────────────────────────────────────────────────────
class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"
    column_list = [User.id, User.email, User.full_name, User.role,
                   User.xp, User.streak, User.is_active, User.is_suspended, User.created_at]
    column_searchable_list = [User.email, User.full_name]
    column_sortable_list = [User.created_at, User.xp, User.streak, User.role]
    column_filters = [
        AllUniqueStringValuesFilter(User.role, title="Role"),
        BooleanFilter(User.is_active, title="Active"),
        BooleanFilter(User.is_suspended, title="Suspended"),
    ]
    column_details_exclude_list = [User.hashed_password]
    form_excluded_columns = [User.hashed_password]
    can_delete = True


class CourseAdmin(ModelView, model=Course):
    name = "Course"
    name_plural = "Courses"
    icon = "fa-solid fa-graduation-cap"
    column_list = [Course.id, Course.title, Course.category, Course.status,
                   Course.is_public, Course.rating, Course.total_enrollments, Course.created_at]
    column_searchable_list = [Course.title, Course.category]
    column_sortable_list = [Course.created_at,
                            Course.rating, Course.total_enrollments]
    column_filters = [
        AllUniqueStringValuesFilter(Course.status, title="Status"),
        BooleanFilter(Course.is_public, title="Public"),
        AllUniqueStringValuesFilter(Course.category, title="Category"),
    ]


class LessonAdmin(ModelView, model=Lesson):
    name = "Lesson"
    name_plural = "Lessons"
    icon = "fa-solid fa-book-open"
    column_list = [Lesson.id, Lesson.course_id, Lesson.title,
                   Lesson.kind, Lesson.position, Lesson.is_free, Lesson.like_count]
    column_searchable_list = [Lesson.title]
    column_filters = [
        AllUniqueStringValuesFilter(Lesson.kind, title="Kind"),
        BooleanFilter(Lesson.is_free, title="Free"),
    ]


class EnrollmentAdmin(ModelView, model=Enrollment):
    name = "Enrollment"
    name_plural = "Enrollments"
    icon = "fa-solid fa-user-plus"
    column_list = [Enrollment.id, Enrollment.user_id, Enrollment.course_id,
                   Enrollment.status, Enrollment.progress, Enrollment.enrolled_at]
    column_filters = [
        AllUniqueStringValuesFilter(Enrollment.status, title="Status"),
    ]
    column_sortable_list = [Enrollment.enrolled_at, Enrollment.progress]


class PaymentAdmin(ModelView, model=Payment):
    name = "Payment"
    name_plural = "Payments"
    icon = "fa-solid fa-credit-card"
    column_list = [Payment.id, Payment.user_id, Payment.course_id,
                   Payment.amount, Payment.currency, Payment.provider,
                   Payment.status, Payment.created_at]
    column_filters = [
        AllUniqueStringValuesFilter(Payment.status, title="Status"),
        AllUniqueStringValuesFilter(Payment.provider, title="Provider"),
        AllUniqueStringValuesFilter(Payment.currency, title="Currency"),
    ]
    column_sortable_list = [Payment.created_at, Payment.amount]
    can_delete = False  # Keep audit trail


class PayoutAdmin(ModelView, model=Payout):
    name = "Payout"
    name_plural = "Payouts"
    icon = "fa-solid fa-money-bill-transfer"
    column_list = [Payout.id, Payout.creator_id, Payout.amount,
                   Payout.currency, Payout.status, Payout.processed_at]
    column_filters = [
        AllUniqueStringValuesFilter(Payout.status, title="Status"),
    ]


class ReviewAdmin(ModelView, model=Review):
    name = "Review"
    name_plural = "Reviews"
    icon = "fa-solid fa-star"
    column_list = [Review.id, Review.course_id, Review.user_id,
                   Review.rating, Review.helpful_count, Review.created_at]
    column_sortable_list = [Review.rating, Review.created_at]


class LessonProgressAdmin(ModelView, model=LessonProgress):
    name = "Lesson Progress"
    name_plural = "Lesson Progress"
    icon = "fa-solid fa-chart-line"
    column_list = [LessonProgress.id, LessonProgress.user_id,
                   LessonProgress.lesson_id, LessonProgress.percent,
                   LessonProgress.completed, LessonProgress.last_seen_at]
    column_filters = [
        BooleanFilter(LessonProgress.completed, title="Completed"),
    ]


class BookingAdmin(ModelView, model=Booking):
    name = "Booking"
    name_plural = "Bookings"
    icon = "fa-solid fa-calendar"
    column_list = [Booking.id, Booking.student_id, Booking.psychologist_id,
                   Booking.date, Booking.time, Booking.status, Booking.price]
    column_filters = [
        AllUniqueStringValuesFilter(Booking.status, title="Status"),
    ]


class PsychologistProfileAdmin(ModelView, model=PsychologistProfile):
    name = "Psychologist Profile"
    name_plural = "Psychologist Profiles"
    icon = "fa-solid fa-user-doctor"
    column_list = [PsychologistProfile.id, PsychologistProfile.user_id,
                   PsychologistProfile.specialization, PsychologistProfile.hourly_rate,
                   PsychologistProfile.is_approved]
    column_filters = [
        BooleanFilter(PsychologistProfile.is_approved, title="Approved"),
    ]


# ── Factory ────────────────────────────────────────────────────────────────────
def create_admin(app) -> Admin:
    authentication_backend = AdminAuth(secret_key=ADMIN_SECRET_KEY)
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=authentication_backend,
        title="CerebroLearn Admin",
        base_url="/admin",
    )
    for view in [
        UserAdmin, CourseAdmin, LessonAdmin,
        EnrollmentAdmin, PaymentAdmin, PayoutAdmin, ReviewAdmin,
        LessonProgressAdmin, BookingAdmin, PsychologistProfileAdmin,
    ]:
        admin.add_view(view)
    return admin
