# Ragbot React frontend

React + Vite chat UI for the FastAPI endpoints in your backend.

## Start it

1. Start FastAPI from the `backend` directory:

   ```powershell
   cd backend
   uvicorn main:app --reload
   ```

2. In another terminal, enter this frontend directory and install/run it:

   ```powershell
   cd path\to\ragbot-frontend
   npm install
   Copy-Item .env.example .env
   npm run dev
   ```

3. Open the Vite URL shown in the terminal (normally `http://localhost:5173`).

The frontend defaults to `http://localhost:8000`. To change the backend URL, set `VITE_API_URL` in `.env`, then restart Vite.

## Backend connection points

The browser calls these routes:

- `GET /threads` to load the chat list
- `POST /threads` to create a chat
- `GET /threads/{thread_id}/messages` to load messages
- `POST /threads/{thread_id}/messages` with `{"role":"user","content":"..."}` to send a message and receive the user/assistant pair
- `DELETE /threads/{thread_id}` to delete a chat

Allow Vite's origin in FastAPI CORS. For local development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)
```

The API response shape for the POST message endpoint should be:

```json
{
  "user_message": {"id": 1, "role": "user", "content": "Hi"},
  "assistant_message": {"id": 2, "role": "assistant", "content": "Hello"}
}
```

If `add_message` returns a different JSON shape, update the `result.user_message` / `result.assistant_message` access in `src/App.jsx` to match it. The GET messages endpoint should return a JSON array with `id`, `role`, `content`, and optionally `created_at` for every row.
