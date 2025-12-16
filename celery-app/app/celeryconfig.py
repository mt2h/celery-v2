import os
from kombu import Queue, Exchange

# BROKER & RESULT BACKEND
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# FAIR DISPATCH
task_acks_late = True
worker_prefetch_multiplier = 1

# MEMORY MANAGEMENT
worker_max_tasks_per_child = 500
worker_max_memory_per_child = 150000  # KB

# TIMEOUTS
task_time_limit = 1800
task_soft_time_limit = 1500

# SERIALIZATION
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']

# QUEUES
task_default_queue = 'default'
task_default_exchange = 'celery'
task_default_routing_key = 'celery'

task_queues = (
    Queue('default', exchange=Exchange('celery', type='direct'), routing_key='celery'),
    Queue('heavy', exchange=Exchange('heavy', type='direct'), routing_key='heavy.tasks'),
)

# ROUTING
task_routes = {
    'app.tasks.cpu_intensive_task': {'queue': 'heavy'},
    'app.tasks.io_intensive_task': {'queue': 'default'},
    'app.tasks.quick_task': {'queue': 'default'},
}

# OTHER
timezone = 'UTC'
enable_utc = True
task_track_started = True
task_send_sent_event = True
worker_send_task_events = True
