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


from app.settings import ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_SECRET_KEY

from app import models
from app.database import engine
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
class UserAdmin(ModelView, model=models.User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"
    column_list = [models.User.id, models.User.email, models.User.full_name, models.User.role,
                   models.User.xp, models.User.streak, models.User.is_active, models.User.is_suspended, models.     User.created_at]
    column_searchable_list = [models.User.email, models.User.full_name]
    column_sortable_list = [models.User.created_at,
                            models.User.xp, models.User.streak, models.User.role]
    column_filters = [
        AllUniqueStringValuesFilter(models.User.role, title="Role"),
        BooleanFilter(models.User.is_active, title="Active"),
        BooleanFilter(models.User.is_suspended, title="Suspended"),
    ]
    column_details_exclude_list = [models.User.hashed_password]
    form_excluded_columns = [models.User.hashed_password]
    can_delete = True


class CourseAdmin(ModelView, model=models.Course):
    name = "Course"
    name_plural = "Courses"
    icon = "fa-solid fa-graduation-cap"
    column_list = [models.Course.id, models.Course.title, models.Course.category, models.Course.status,
                   models.Course.is_public, models.Course.rating, models.Course.total_enrollments,
                   models.Course.created_at]
    column_searchable_list = [models.Course.title, models.Course.category]
    column_sortable_list = [models.Course.created_at,
                            models.Course.rating, models.Course.total_enrollments]
    column_filters = [
        AllUniqueStringValuesFilter(models.Course.status, title="Status"),
        BooleanFilter(models.Course.is_public, title="Public"),
        AllUniqueStringValuesFilter(models.Course.category, title="Category"),
    ]


class LessonAdmin(ModelView, model=models.Lesson):
    name = "Lesson"
    name_plural = "Lessons"
    icon = "fa-solid fa-book-open"
    column_list = [models.Lesson.id, models.Lesson.title,
                   models.Lesson.kind, models.Lesson.position, models.Lesson.is_free, models.Lesson.like_count]
    column_searchable_list = [models.Lesson.title]
    column_filters = [
        AllUniqueStringValuesFilter(models.Lesson.kind, title="Kind"),
        BooleanFilter(models.Lesson.is_free, title="Free"),
    ]


class EnrollmentAdmin(ModelView, model=models.Enrollment):
    name = "Enrollment"
    name_plural = "Enrollments"
    icon = "fa-solid fa-user-plus"
    column_list = [models.Enrollment.id, models.Enrollment.user_id, models.Enrollment.course_id,
                   models.Enrollment.status, models.Enrollment.progress, models.Enrollment.enrolled_at]
    column_filters = [
        AllUniqueStringValuesFilter(models.Enrollment.status, title="Status"),
    ]
    column_sortable_list = [
        models.Enrollment.enrolled_at, models.Enrollment.progress]


class PaymentAdmin(ModelView, model=models.Payment):
    name = "Payment"
    name_plural = "Payments"
    icon = "fa-solid fa-credit-card"
    column_list = [models.Payment.id, models.Payment.user_id, models.Payment.course_id,
                   models.Payment.amount, models.Payment.currency, models.Payment.provider,
                   models.Payment.status, models.Payment.created_at]
    column_filters = [
        AllUniqueStringValuesFilter(models.Payment.status, title="Status"),
        AllUniqueStringValuesFilter(models.Payment.provider, title="Provider"),
        AllUniqueStringValuesFilter(models.Payment.currency, title="Currency"),
    ]
    column_sortable_list = [models.Payment.created_at, models.Payment.amount]
    can_delete = False  # Keep audit trail


class PayoutAdmin(ModelView, model=models.Payout):
    name = "Payout"
    name_plural = "Payouts"
    icon = "fa-solid fa-money-bill-transfer"
    column_list = [models.Payout.id, models.Payout.creator_id, models.Payout.amount,
                   models.Payout.currency, models.Payout.status, models.Payout.processed_at]
    column_filters = [
        AllUniqueStringValuesFilter(models.Payout.status, title="Status"),
    ]


class ReviewAdmin(ModelView, model=models.Review):
    name = "Review"
    name_plural = "Reviews"
    icon = "fa-solid fa-star"
    column_list = [models.Review.id, models.Review.course_id, models.Review.user_id,
                   models.Review.rating, models.Review.helpful_count, models.Review.created_at]
    column_sortable_list = [models.Review.rating, models.Review.created_at]


class LessonProgressAdmin(ModelView, model=models.LessonProgress):
    name = "Lesson Progress"
    name_plural = "Lesson Progress"
    icon = "fa-solid fa-chart-line"
    column_list = [models.LessonProgress.id, models.LessonProgress.user_id,
                   models.LessonProgress.lesson_id, models. LessonProgress.percent,
                   models.LessonProgress.completed, models.LessonProgress.last_seen_at]
    column_filters = [
        BooleanFilter(models.LessonProgress.completed, title="Completed"),
    ]


class BookingAdmin(ModelView, model=models.Booking):
    name = "Booking"
    name_plural = "Bookings"
    icon = "fa-solid fa-calendar"
    column_list = [models.Booking.id, models.Booking.student_id, models.Booking.psychologist_id,
                   models.Booking.date, models.Booking.time, models.Booking.status, models.Booking.price]
    column_filters = [
        AllUniqueStringValuesFilter(models.Booking.status, title="Status"),
    ]


class PsychologistProfileAdmin(ModelView, model=models.PsychologistProfile):
    name = "Psychologist Profile"
    name_plural = "Psychologist Profiles"
    icon = "fa-solid fa-user-doctor"
    column_list = [models.PsychologistProfile.id, models.PsychologistProfile.user_id,
                   models.PsychologistProfile.specialization, models.PsychologistProfile.hourly_rate,
                   models.  PsychologistProfile.is_approved]
    column_filters = [
        BooleanFilter(models.PsychologistProfile.is_approved,
                      title="Approved"),
    ]


class SectionAdmin(ModelView, model=models.Section):
    name = "Section"
    name_plural = "Sections"
    icon = "fa-solid fa-list"
    column_list = [models.Section.id, models.Section.title, models.Section.course_id,
                   models.Section.order, models.Section.duration, models.Section.created_at]
    column_searchable_list = [models.Section.title]
    column_sortable_list = [models.Section.order, models.Section.created_at]


class PsychologistInviteAdmin(ModelView, model=models.PsychologistInvite):
    name = "Psychologist Invite"
    name_plural = "Psychologist Invites"
    icon = "fa-solid fa-envelope"
    column_list = [models.PsychologistInvite.id, models.PsychologistInvite.email,
                   models.PsychologistInvite.status, models.PsychologistInvite.invited_by,
                   models.PsychologistInvite.expires_at, models.PsychologistInvite.created_at]
    column_searchable_list = [models.   PsychologistInvite.email]
    column_filters = [
        AllUniqueStringValuesFilter(
            models.PsychologistInvite.status, title="Status"),
    ]
    column_sortable_list = [models.PsychologistInvite.created_at]
    can_delete = False


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
        UserAdmin, CourseAdmin, SectionAdmin, LessonAdmin,
        EnrollmentAdmin, PaymentAdmin, PayoutAdmin, ReviewAdmin,
        LessonProgressAdmin, BookingAdmin, PsychologistProfileAdmin,
        PsychologistInviteAdmin,
    ]:
        admin.add_view(view)
    return admin
