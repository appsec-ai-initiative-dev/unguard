# Agent Scheduling and HTTP Triggering System

This implementation adds agent scheduling and HTTP triggering capabilities to the like-service. The system allows agents to run both periodically via Laravel's built-in scheduler and on-demand via HTTP requests.

## Features

### 1. Periodic Scheduling
The system uses Laravel's built-in task scheduler to run agent tasks at regular intervals:

- **Monitor Task**: Runs every minute for continuous system health monitoring
- **Cleanup Task**: Runs every 5 minutes for maintenance operations  
- **Backup Task**: Runs every hour for data backup operations

### 2. HTTP Triggering
Agents can also be triggered externally via HTTP requests:

- **Status Endpoint**: `GET /agent/status` - Returns agent status and available tasks
- **Trigger Endpoint**: `POST /agent/trigger` - Executes a specific agent task

## Implementation

### Files Modified/Created

1. **`app/Console/Commands/AgentCommand.php`** - Main agent command implementation
2. **`app/Console/Kernel.php`** - Scheduler configuration
3. **`app/Http/Controllers/AgentController.php`** - HTTP trigger controller
4. **`routes/web.php`** - HTTP routes for agent endpoints

### Agent Tasks

The system supports multiple task types:

- `default` - General agent operations
- `cleanup` - Cleanup and maintenance operations
- `monitor` - System health monitoring
- `backup` - Data backup operations

## Usage

### Scheduled Execution

To enable scheduled execution, run the Laravel scheduler:

```bash
# For development/testing - runs scheduler manually
php artisan schedule:run

# For production - add to crontab to run every minute
* * * * * cd /path/to/project && php artisan schedule:run >> /dev/null 2>&1
```

### Manual Command Execution

You can also run agent tasks manually:

```bash
# Run default task
php artisan agent:run

# Run specific task
php artisan agent:run --task=cleanup
php artisan agent:run --task=monitor
php artisan agent:run --task=backup
```

### HTTP Triggering

#### Get Agent Status
```bash
curl -X GET http://your-domain/agent/status
```

Response:
```json
{
  "status": "active",
  "available_tasks": ["default", "cleanup", "monitor", "backup"],
  "message": "Agent is ready to receive tasks",
  "timestamp": "2025-09-04 15:18:50",
  "triggers": {
    "scheduled": {
      "monitor": "Every minute",
      "cleanup": "Every 5 minutes",
      "backup": "Every hour"
    },
    "http": {
      "endpoint": "/agent/trigger",
      "method": "POST",
      "parameters": {
        "task": "Task name (optional, defaults to \"default\")"
      }
    }
  }
}
```

#### Trigger Agent Task
```bash
# Trigger default task
curl -X POST http://your-domain/agent/trigger

# Trigger specific task
curl -X POST http://your-domain/agent/trigger \
  -H "Content-Type: application/json" \
  -d '{"task": "cleanup"}'
```

Response:
```json
{
  "status": "success",
  "message": "Agent task executed successfully",
  "task": "cleanup",
  "timestamp": "2025-09-04 15:18:50",
  "output": "Agent started at: 2025-09-04 15:18:50\nExecuting task: cleanup\nPerforming cleanup operations...\nCleanup completed\nAgent task completed successfully"
}
```

## Monitoring and Logging

All agent executions are logged with the following information:

- Task name
- Execution timestamp
- Trigger source (scheduler vs HTTP)
- IP address and user agent (for HTTP triggers)
- Execution results

Logs can be found in Laravel's standard log files (`storage/logs/laravel.log`).

## Security Considerations

- The HTTP trigger endpoints do not require authentication in this basic implementation
- For production use, consider adding authentication/authorization
- Input validation is performed on task parameters
- All requests are logged for audit purposes

## Extending the System

To add new agent tasks:

1. Add new case to the `handle()` method in `AgentCommand.php`
2. Implement the task-specific logic as a private method
3. Optionally add scheduled execution in `Kernel.php`
4. Update the available tasks list in `AgentController.php`

This implementation provides a foundation for building more complex agent systems while maintaining simplicity and using Laravel's built-in capabilities.