from src.configs.celery_config import celery_app
import sys
import os
import redis
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("worker.log")
    ]
)

logger = logging.getLogger(__name__)

# Add the src directory to the path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.append(src_path)

# Set environment variables to help with memory management
os.environ['OMP_NUM_THREADS'] = '1'  # Limit OpenMP threads
os.environ['MKL_NUM_THREADS'] = '1'  # Limit MKL threads

def check_redis_connection():
    """Check if Redis is available before starting worker."""
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    try:
        r = redis.from_url(redis_url)
        r.ping()
        logger.info("✅ Redis connection successful")
        return True
    except redis.exceptions.ConnectionError as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False

def get_worker_args():
    """Get command-line arguments for Celery worker."""
    
    # Default arguments
    worker_args = ['worker', '--loglevel=info']
    
    # Check if we're in a resource-intensive environment
    if os.environ.get('RESOURCE_INTENSIVE', 'false').lower() == 'true':
        # Use solo pool for resource-intensive tasks like embeddings
        worker_args.extend([
            '--pool=solo',
            '--concurrency=1',
            '--max-tasks-per-child=1'
        ])
        logger.info("🔧 Using solo pool for resource-intensive tasks")
    else:
        # Use prefork pool for regular tasks
        worker_args.extend([
            '--pool=prefork',
            '--concurrency=2',
            '--max-tasks-per-child=10'
        ])
        logger.info("🔧 Using prefork pool for regular tasks")
    
    # Optional queue selection
    queue = os.environ.get('CELERY_QUEUE')
    if queue:
        worker_args.extend(['-Q', queue])
        logger.info(f"📨 Processing tasks from queue: {queue}")
    
    return worker_args

if __name__ == '__main__':
    # Check for Redis availability
    if not check_redis_connection():
        logger.warning("⚠️ Proceeding without Redis connection confirmation")
    
    # Import tasks here to avoid circular imports
    logger.info("🔄 Importing task modules...")
    from src.tasks.celery_tasks import (
        create_consultant_primer, 
        create_personalized_email,
        create_embed_documents,
        create_summariser_task
    )
    logger.info("✅ Task modules imported successfully")
    
    # Start the worker
    worker_args = get_worker_args()
    logger.info(f"🚀 Starting Celery worker with args: {' '.join(worker_args)}")
    celery_app.worker_main(worker_args)