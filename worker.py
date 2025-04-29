from src.configs.celery_config import celery_app
import sys
import os
import redis
# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == '__main__':
    # Make sure all task modules are imported
    from src.tasks.celery_tasks import create_consultant_primer, create_personalized_email
    
    celery_app.worker_main(['worker', '--loglevel=info', '-c', '2'])