First: docker run -p 6333:6333 qdrant/qdrant
check : http://localhost:6333


Second (local): uvicorn app.main:app --reload
Check : http://127.0.0.1:8000/docs

Render start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT


Third: python ui.py
check: http://127.0.0.1:7860
