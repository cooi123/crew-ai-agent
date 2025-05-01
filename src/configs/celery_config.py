from celery import Celery
from dotenv import load_dotenv
load_dotenv()
import os

celery_app = Celery(
    'studio_agents',
    broker= os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
)

celery_app.conf.update(

    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_always_eager=False,  # Set to True for debugging
    worker_max_memory_per_child=1000000,  # 1GB in KB, adjust as needed
    worker_max_tasks_per_child=10, 
    task_time_limit=3600,                 # Hard time limit (1 hour)
    task_soft_time_limit=3000,  
    
)