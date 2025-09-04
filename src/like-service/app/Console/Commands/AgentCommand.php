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

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\Log;

class AgentCommand extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'agent:run {--task=default : The task to run}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Run agent task - can be scheduled or triggered externally';

    /**
     * Create a new command instance.
     *
     * @return void
     */
    public function __construct()
    {
        parent::__construct();
    }

    /**
     * Execute the console command.
     *
     * @return int
     */
    public function handle()
    {
        $task = $this->option('task');
        $timestamp = now()->toDateTimeString();
        
        $this->info("Agent started at: {$timestamp}");
        $this->info("Executing task: {$task}");
        
        // Log the execution for monitoring
        Log::info("Agent task executed", [
            'task' => $task,
            'timestamp' => $timestamp,
            'triggered_by' => 'scheduler'
        ]);
        
        // Simulate some agent work
        switch ($task) {
            case 'cleanup':
                $this->performCleanup();
                break;
            case 'monitor':
                $this->performMonitoring();
                break;
            case 'backup':
                $this->performBackup();
                break;
            default:
                $this->performDefaultTask();
                break;
        }
        
        $this->info("Agent task completed successfully");
        return 0;
    }
    
    /**
     * Perform cleanup task
     */
    private function performCleanup()
    {
        $this->info("Performing cleanup operations...");
        // Simulate cleanup work
        sleep(2);
        $this->info("Cleanup completed");
    }
    
    /**
     * Perform monitoring task
     */
    private function performMonitoring()
    {
        $this->info("Performing system monitoring...");
        // Simulate monitoring work
        sleep(1);
        $this->info("Monitoring completed - system healthy");
    }
    
    /**
     * Perform backup task
     */
    private function performBackup()
    {
        $this->info("Performing backup operations...");
        // Simulate backup work
        sleep(3);
        $this->info("Backup completed");
    }
    
    /**
     * Perform default task
     */
    private function performDefaultTask()
    {
        $this->info("Performing default agent operations...");
        // Simulate default work
        sleep(1);
        $this->info("Default task completed");
    }
}