# CerebroLearn — LLM Integration Guide
# Migrating the Frontend from Supabase to FastAPI

> **Read this first.** This guide is written for an AI agent. It tells you exactly which files
> to change, which lines to change, and what to replace them with to connect the frontend to the
> new FastAPI backend instead of Supabase. Do NOT touch any file inside `backend/`. Only touch
> files inside `src/`.

---

## CONTEXT: What changed

The backend was a Supabase Edge Function (Deno) with a single flat KV table.
It is now a **FastAPI + PostgreSQL** server running at `http://localhost:8000`.
All API paths now start with `/api` instead of being on the Supabase functions URL.

---

## STEP 1 — `src/utils/api-client.ts` — THE main file to change

Open this file. Make all changes below in order.

### 1a. Delete the Supabase import (line 2)

Find and delete this line:
```ts
import { projectId, publicAnonKey } from './supabase/info';
```

### 1b. Change BASE_URL (line 17)

**Find:**
```ts
const BASE_URL = `https://${projectId}.supabase.co/functions/v1/make-server-c6a99485`;
```
**Replace with:**
```ts
const BASE_URL = 'http://localhost:8000/api';
```

### 1c. Change how the auth token is read (lines 20–31)

**Find this entire function and replace it:**
```ts
// OLD — reads Supabase session
function getAuthToken(): string | null {
  try {
    const session = localStorage.getItem('supabase.auth.token');
    if (session) {
      const parsed = JSON.parse(session);
      return parsed.access_token || null;
    }
  } catch (error) {
    console.error('Error getting auth token:', error);
  }
  return null;
}
```
**Replace with:**
```ts
// NEW — reads FastAPI JWT stored after login
function getAuthToken(): string | null {
  return localStorage.getItem('cerebrolearn.auth.token');
}
```

### 1d. Remove the Supabase anon key fallback (inside the `request` function)

**Find:**
```ts
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  } else {
    headers['Authorization'] = `Bearer ${publicAnonKey}`;
  }
```
**Replace with:**
```ts
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
```

### 1e. Rewrite `authApi` — login endpoint is new, paths changed

**Replace the entire `authApi` object with:**
```ts
export const authApi = {
  signup: (data: {
    email: string; password: string; full_name: string;
    role?: string; org_id?: string;
  }) => request<{ success: boolean; user: User }>('/auth/signup', {
    method: 'POST', body: JSON.stringify(data),
  }),

  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; token_type: string; user: User }>('/auth/login', {
      method: 'POST', body: JSON.stringify(data),
    }),

  getProfile: () => request<User>('/accounts/profile'),

  updateProfile: (updates: Partial<User>) =>
    request<User>('/accounts/profile', { method: 'PUT', body: JSON.stringify(updates) }),
};
```

> **After a successful `authApi.login()` call, save the token:**
> ```ts
> localStorage.setItem('cerebrolearn.auth.token', result.access_token);
> ```
> **To log out:** `localStorage.removeItem('cerebrolearn.auth.token');`

### 1f. Fix `coursesApi` — list is now paginated

**Find:**
```ts
  getAll: () => request<{ courses: Course[] }>('/courses'),
```
**Replace with:**
```ts
  getAll: () => request<{ items: Course[]; total: number; page: number; pages: number }>('/courses/'),
```

**Find:**
```ts
  getById: (courseId: string) =>
    request<{ course: Course; lessons: Lesson[] }>(`/courses/${courseId}`),
```
**Replace with:**
```ts
  getById: (courseId: string) =>
    request<Course & { lessons: Lesson[] }>(`/courses/${courseId}`),
```

Also add trailing slash to the create path: `/courses` → `/courses/`

### 1g. Replace `socialApi` — like/bookmark paths moved under `/lessons/{id}/...`

**Replace the entire `socialApi` object with:**
```ts
export const socialApi = {
  like: (lessonId: string) =>
    request<{ success: boolean; likes: number }>(`/lessons/${lessonId}/like`, { method: 'POST' }),

  unlike: (lessonId: string) =>
    request<{ success: boolean; likes: number }>(`/lessons/${lessonId}/like`, { method: 'DELETE' }),

  bookmark: (lessonId: string) =>
    request<{ success: boolean }>(`/lessons/${lessonId}/bookmark`, { method: 'POST' }),

  getBookmarks: () => request<any[]>('/bookmarks/'),

  addComment: (data: { lesson_id: string; content: string; parent_id?: string }) =>
    request<Comment>('/comments/', { method: 'POST', body: JSON.stringify(data) }),

  // share is NOT implemented in the FastAPI backend — return a no-op
  share: (_lessonId: string, _platform: string) =>
    Promise.resolve({ success: false, shares: 0 }),
};
```

### 1h. Fix `gamificationApi` — leaderboard returns array directly

**Find:**
```ts
  getLeaderboard: () => request<{ leaderboard: User[] }>('/leaderboard'),
```
**Replace with:**
```ts
  getLeaderboard: () => request<User[]>('/leaderboard/'),
```

Also stub out `awardBadge` — it is not implemented:
```ts
  awardBadge: (_data: any) => Promise.resolve({ success: false, badges: [] }),
```

### 1i. Fix `adminApi` — users and courses are now paginated

**Find:**
```ts
  getUsers: () => request<{ users: User[] }>('/admin/users'),
  getCourses: () => request<{ courses: Course[] }>('/admin/courses'),
```
**Replace with:**
```ts
  getUsers: () => request<{ items: User[]; total: number }>('/admin/users'),
  getCourses: () => request<{ items: Course[]; total: number }>('/admin/courses'),
```

### 1j. Stub out unimplemented endpoints

These endpoints have NO FastAPI route. Replace them with stubs so the app does not crash:

```ts
export const quizApi = {
  submitAttempt: (_data: any) => Promise.resolve({ success: false, attempt: null }),
};

export const organizationsApi = {
  create: (_data: any) => Promise.resolve({ success: false, organization: null }),
  getById: (_orgId: string) => Promise.resolve({ organization: null }),
};
```

---

## STEP 2 — `src/utils/fetchInterceptor.ts` — Disable the mock interceptor

This file currently intercepts ALL fetch calls and returns fake data for the old Supabase URL.
After you change `BASE_URL` in Step 1, the interceptor will no longer match FastAPI calls
(since they go to `localhost:8000`, not `supabase.co`), so FastAPI calls will pass through correctly.

**But you must still disable the interceptor being initialized.** Search the codebase for:
```ts
initializeFetchInterceptor()
```
Find the file that imports and calls it (likely `src/main.tsx` or `src/App.tsx`) and delete that call.
The interceptor was only needed while in Supabase offline/demo mode.

---

## STEP 3 — Find and replace Supabase Auth calls across the app

Search the entire `src/` folder for these patterns and replace them:

| Search for | Replace with |
|---|---|
| `supabase.auth.signInWithPassword(...)` | `authApi.login({ email, password })` then save token |
| `supabase.auth.signUp(...)` | `authApi.signup({ email, password, full_name })` |
| `supabase.auth.signOut()` | `localStorage.removeItem('cerebrolearn.auth.token')` |
| `supabase.auth.getSession()` | `authApi.getProfile()` |
| `supabase.auth.getUser()` | `authApi.getProfile()` |
| `supabase.auth.token` in localStorage | `cerebrolearn.auth.token` in localStorage |

---

## STEP 4 — Response shape changes summary

When the frontend reads response data, update any code that destructures these shapes:

| Data | Old shape | New shape |
|---|---|---|
| Course list | `{ courses: [...] }` | `{ items: [...], total, page, pages }` — use `.items` |
| Single course+lessons | `{ course: {...}, lessons: [...] }` | `{ ...courseFields, lessons: [...] }` — no wrapper |
| Profile | `{ user: {...} }` | `{...userFields}` — direct object, no wrapper |
| Comment | `{ success, comment: {...} }` | `{...commentFields}` — direct object |
| Bookmarks | `{ bookmarks: [...] }` | `[...]` — direct array |
| Leaderboard | `{ leaderboard: [...] }` | `[...]` — direct array |
| Admin users | `{ users: [...] }` | `{ items: [...], total, page, pages }` |
| Admin courses | `{ courses: [...] }` | `{ items: [...], total, page, pages }` |

---

## STEP 5 — Full endpoint mapping table (Supabase path → FastAPI path)

| Old path | New path | Method | Change in response |
|---|---|---|---|
| `/signup` | `/api/auth/signup` | POST | Same |
| *(Supabase Auth)* | `/api/auth/login` | POST | NEW — returns `access_token` |
| `/profile` GET | `/api/accounts/profile` | GET | Direct user object |
| `/profile` PUT | `/api/accounts/profile` | PUT | Direct user object |
| `/courses` GET | `/api/courses/` | GET | Paginated |
| `/courses` POST | `/api/courses/` | POST | Direct course object |
| `/courses/{id}` GET | `/api/courses/{id}` | GET | Merged course+lessons |
| `/courses/{id}` PUT | `/api/courses/{id}` | PUT | Direct course object |
| `/courses/{id}/reviews` | `/api/courses/{id}/reviews` | GET | Direct array |
| `/lessons` POST | `/api/lessons/` | POST | Direct lesson object |
| `/lessons/{id}` GET | `/api/lessons/{id}` | GET | Same |
| `/lessons/{id}/comments` | `/api/lessons/{id}/comments` | GET | Direct array |
| `/likes` POST `{lesson_id}` | `/api/lessons/{lesson_id}/like` | POST | No body |
| `/likes/{id}` DELETE | `/api/lessons/{lesson_id}/like` | DELETE | No body |
| `/bookmarks` POST `{lesson_id}` | `/api/lessons/{lesson_id}/bookmark` | POST | No body |
| `/bookmarks` GET | `/api/bookmarks/` | GET | Direct array |
| `/comments` POST | `/api/comments/` | POST | Direct comment object |
| `/enrollments` GET | `/api/enrollments/` | GET | Direct array |
| `/enrollments` POST | `/api/enrollments/` | POST | Direct enrollment object |
| `/progress` POST | `/api/progress/` | POST | Direct progress object |
| `/progress/{id}` GET | `/api/progress/{id}` | GET | Same |
| `/reviews` POST | `/api/reviews/` | POST | Direct review object |
| `/leaderboard` GET | `/api/leaderboard/` | GET | Direct array |
| `/creator/courses` | `/api/creator/courses` | GET | Direct array |
| `/creator/courses/{id}/subscribers` | `/api/creator/courses/{id}/subscribers` | GET | Direct array |
| `/creator/courses/{id}/analytics` | `/api/creator/courses/{id}/analytics` | GET | Same |
| `/creator/earnings` | `/api/creator/earnings` | GET | Same |
| `/payments` POST | `/api/payments/` | POST | Same |
| `/payments/{id}` PUT | `/api/payments/{id}` | PUT | Same |
| `/admin/users` | `/api/admin/users` | GET | Paginated |
| `/admin/courses` | `/api/admin/courses` | GET | Paginated |
| `/admin/analytics` | `/api/admin/analytics` | GET | Same |
| `/admin/users/{id}/role` | `/api/admin/users/{id}/role` | PUT | Same |
| `/admin/users/{id}/status` | `/api/admin/users/{id}/status` | PUT | Same |
| `/admin/settings` | `/api/admin/settings` | GET/PUT | Same |
| `/quiz-attempts` | ❌ NOT IMPLEMENTED | — | Return stub |
| `/badges` | ❌ NOT IMPLEMENTED | — | Return stub |
| `/shares` | ❌ NOT IMPLEMENTED | — | Return stub |
| `/organizations` | ❌ NOT IMPLEMENTED | — | Return stub |

---

## STEP 6 — Verify the connection works

1. Start the FastAPI server: `cd backend && PYTHONPATH=. python3 -m uvicorn app.main:app --reload --port 8000`
2. In the browser console: `await fetch('http://localhost:8000/health').then(r=>r.json())`
   → should return `{ "status": "ok", "service": "CerebroLearn" }`
3. Open `http://localhost:8000/docs` — full live Swagger UI with all endpoints
4. Sign up a user → check `localStorage.getItem('cerebrolearn.auth.token')` is set

---

## Admin UI

- URL: `http://localhost:8000/admin`
- Username: `admin` (set `ADMIN_USERNAME` in `backend/.env` to change)
- Password: `CerebroAdmin2025!` (set `ADMIN_PASSWORD` in `backend/.env` to change)

