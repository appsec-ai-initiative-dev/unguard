<?php
#
# Copyright 2023 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Log;

class AgentController
{
    /**
     * Trigger agent via HTTP request
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function trigger(Request $request): JsonResponse
    {
        $task = $request->input('task', 'default');
        $timestamp = now()->toDateTimeString();
        
        try {
            // Log the HTTP trigger
            Log::info("Agent triggered via HTTP", [
                'task' => $task,
                'timestamp' => $timestamp,
                'triggered_by' => 'http_request',
                'ip' => $request->ip(),
                'user_agent' => $request->userAgent()
            ]);
            
            // Execute the agent command
            $exitCode = Artisan::call('agent:run', [
                '--task' => $task
            ]);
            
            $output = Artisan::output();
            
            if ($exitCode === 0) {
                return response()->json([
                    'status' => 'success',
                    'message' => 'Agent task executed successfully',
                    'task' => $task,
                    'timestamp' => $timestamp,
                    'output' => trim($output)
                ], 200);
            } else {
                return response()->json([
                    'status' => 'error',
                    'message' => 'Agent task failed',
                    'task' => $task,
                    'timestamp' => $timestamp,
                    'output' => trim($output)
                ], 500);
            }
        } catch (\Exception $e) {
            Log::error("Agent HTTP trigger failed", [
                'error' => $e->getMessage(),
                'task' => $task,
                'timestamp' => $timestamp
            ]);
            
            return response()->json([
                'status' => 'error',
                'message' => 'Failed to trigger agent: ' . $e->getMessage(),
                'task' => $task,
                'timestamp' => $timestamp
            ], 500);
        }
    }
    
    /**
     * Get agent status and available tasks
     *
     * @return JsonResponse
     */
    public function status(): JsonResponse
    {
        $availableTasks = ['default', 'cleanup', 'monitor', 'backup'];
        
        return response()->json([
            'status' => 'active',
            'available_tasks' => $availableTasks,
            'message' => 'Agent is ready to receive tasks',
            'timestamp' => now()->toDateTimeString(),
            'triggers' => [
                'scheduled' => [
                    'monitor' => 'Every minute',
                    'cleanup' => 'Every 5 minutes', 
                    'backup' => 'Every hour'
                ],
                'http' => [
                    'endpoint' => '/agent/trigger',
                    'method' => 'POST',
                    'parameters' => ['task' => 'Task name (optional, defaults to "default")']
                ]
            ]
        ]);
    }
}