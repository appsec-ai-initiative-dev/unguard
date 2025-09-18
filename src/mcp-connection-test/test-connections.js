#!/usr/bin/env node

/*
 * Copyright 2024 Dynatrace LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

const http = require('http');
const https = require('https');
const url = require('url');

/**
 * MCP (Microservice Communication Protocol) Connection Test
 * 
 * This test validates connectivity between all Unguard microservices
 * by checking health endpoints and basic service communication paths.
 */

class MCPConnectionTest {
    constructor() {
        this.services = this.buildServiceConfig();
        this.results = [];
        this.timeout = 10000; // 10 seconds timeout per service
    }

    buildServiceConfig() {
        // Build service configuration from environment variables
        // These match the values.yaml configuration from the Helm chart
        return [
            {
                name: 'frontend-nextjs',
                url: `http://${process.env.FRONTEND_ADDRESS || 'unguard-frontend-nextjs'}/ui/api/healthz`,
                description: 'Frontend health endpoint'
            },
            {
                name: 'status-service',
                url: `http://${process.env.STATUS_SERVICE_ADDRESS || 'unguard-status-service'}${process.env.STATUS_SERVICE_BASE_PATH || '/status-service'}/deployments/health`,
                description: 'Status service deployment health'
            },
            {
                name: 'profile-service',
                url: `http://${process.env.PROFILE_SERVICE_ADDRESS || 'unguard-profile-service'}/healthz`,
                description: 'Profile service health endpoint'
            },
            {
                name: 'microblog-service',
                url: `http://${process.env.MICROBLOG_SERVICE_ADDRESS || 'unguard-microblog-service'}/timeline`,
                description: 'Microblog service timeline endpoint (basic connectivity)'
            },
            {
                name: 'user-auth-service',
                url: `http://${process.env.USER_AUTH_SERVICE_ADDRESS || 'unguard-user-auth-service'}/user-auth-service/register`,
                description: 'User auth service connectivity (register endpoint for basic check)'
            },
            {
                name: 'membership-service',
                url: `http://${process.env.MEMBERSHIP_SERVICE_ADDRESS || 'unguard-membership-service'}${process.env.MEMBERSHIP_SERVICE_BASE_PATH || '/membership-service'}/test`,
                description: 'Membership service connectivity',
                method: 'GET',
                expectStatus: [404, 405] // Expecting method not allowed or not found, which indicates service is running
            },
            {
                name: 'like-service', 
                url: `http://${process.env.LIKE_SERVICE_ADDRESS || 'unguard-like-service'}${process.env.LIKE_SERVICE_BASE_PATH || '/like-service'}/health`,
                description: 'Like service connectivity',
                method: 'GET',
                expectStatus: [200, 404, 405] // Service might not have a health endpoint
            },
            {
                name: 'payment-service',
                url: `http://${process.env.PAYMENT_SERVICE_ADDRESS || 'unguard-payment-service'}/health`,
                description: 'Payment service connectivity',
                method: 'GET',
                expectStatus: [200, 404, 405] // Service might not have a health endpoint
            },
            {
                name: 'proxy-service',
                url: `http://${process.env.PROXY_SERVICE_ADDRESS || 'unguard-proxy-service'}/proxy-service/health`,
                description: 'Proxy service connectivity',
                method: 'GET', 
                expectStatus: [200, 404, 405] // Service might not have a health endpoint
            },
            {
                name: 'ad-service',
                url: `http://${process.env.AD_SERVICE_ADDRESS || 'unguard-ad-service'}${process.env.AD_SERVICE_BASE_PATH || '/ad-service'}/ad`,
                description: 'Ad service connectivity',
                method: 'GET',
                expectStatus: [200, 404] // Ad service should respond to basic requests
            }
        ];
    }

    async testServiceConnection(service) {
        const startTime = Date.now();
        let result = {
            name: service.name,
            url: service.url,
            description: service.description,
            status: 'UNKNOWN',
            responseTime: 0,
            statusCode: null,
            error: null
        };

        try {
            console.log(`Testing ${service.name}: ${service.url}`);
            
            const response = await this.makeHttpRequest(service.url, service.method || 'GET');
            result.responseTime = Date.now() - startTime;
            result.statusCode = response.statusCode;

            // Check if status code is expected
            const expectedStatuses = service.expectStatus || [200];
            if (expectedStatuses.includes(response.statusCode)) {
                result.status = 'PASS';
                console.log(`✅ ${service.name}: Connected (${response.statusCode}) - ${result.responseTime}ms`);
            } else {
                result.status = 'FAIL';
                result.error = `Unexpected status code: ${response.statusCode}`;
                console.log(`❌ ${service.name}: Unexpected status ${response.statusCode} - ${result.responseTime}ms`);
            }

        } catch (error) {
            result.responseTime = Date.now() - startTime;
            result.error = error.message;
            
            // Network errors or timeouts are failures
            if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND' || error.code === 'ETIMEDOUT') {
                result.status = 'FAIL';
                console.log(`❌ ${service.name}: Connection failed - ${error.message}`);
            } else if (error.statusCode) {
                // Service responded but with an error status
                result.statusCode = error.statusCode;
                const expectedStatuses = service.expectStatus || [200];
                if (expectedStatuses.includes(error.statusCode)) {
                    result.status = 'PASS';
                    console.log(`✅ ${service.name}: Connected (${error.statusCode}) - ${result.responseTime}ms`);
                } else {
                    result.status = 'FAIL';
                    console.log(`❌ ${service.name}: HTTP ${error.statusCode} - ${result.responseTime}ms`);
                }
            } else {
                result.status = 'FAIL';
                console.log(`❌ ${service.name}: Request failed - ${error.message}`);
            }
        }

        return result;
    }

    makeHttpRequest(requestUrl, method) {
        return new Promise((resolve, reject) => {
            const urlObj = new URL(requestUrl);
            const isHttps = urlObj.protocol === 'https:';
            const httpModule = isHttps ? https : http;
            
            const options = {
                hostname: urlObj.hostname,
                port: urlObj.port || (isHttps ? 443 : 80),
                path: urlObj.pathname + urlObj.search,
                method: method,
                timeout: this.timeout,
                headers: {
                    'User-Agent': 'MCP-Connection-Test/1.0'
                }
            };

            const req = httpModule.request(options, (res) => {
                // Don't read the body, just get the status code
                res.on('data', () => {}); // Consume the data
                res.on('end', () => {
                    resolve({
                        statusCode: res.statusCode,
                        headers: res.headers
                    });
                });
            });

            req.on('timeout', () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.end();
        });
    }

    async runAllTests() {
        console.log('🚀 Starting MCP (Microservice Communication Protocol) Connection Tests');
        console.log(`Testing ${this.services.length} services...`);
        console.log('='.repeat(80));

        const promises = this.services.map(service => this.testServiceConnection(service));
        this.results = await Promise.all(promises);

        return this.generateReport();
    }

    generateReport() {
        console.log('\n' + '='.repeat(80));
        console.log('📊 MCP CONNECTION TEST RESULTS');
        console.log('='.repeat(80));

        const passed = this.results.filter(r => r.status === 'PASS').length;
        const failed = this.results.filter(r => r.status === 'FAIL').length;
        const unknown = this.results.filter(r => r.status === 'UNKNOWN').length;

        console.log(`Total Services: ${this.results.length}`);
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`❓ Unknown: ${unknown}`);
        console.log();

        // Detailed results
        this.results.forEach(result => {
            const status = result.status === 'PASS' ? '✅' : result.status === 'FAIL' ? '❌' : '❓';
            console.log(`${status} ${result.name.padEnd(20)} | ${result.statusCode || 'N/A'} | ${result.responseTime}ms | ${result.error || 'OK'}`);
        });

        console.log('\n' + '='.repeat(80));

        // Return overall test result
        const overallSuccess = failed === 0;
        if (overallSuccess) {
            console.log('🎉 All MCP connections are healthy!');
        } else {
            console.log(`⚠️  ${failed} service(s) failed connection tests`);
        }

        return {
            success: overallSuccess,
            summary: {
                total: this.results.length,
                passed,
                failed,
                unknown
            },
            results: this.results
        };
    }
}

// Main execution
async function main() {
    const test = new MCPConnectionTest();
    
    try {
        const report = await test.runAllTests();
        
        // Exit with appropriate code
        process.exit(report.success ? 0 : 1);
        
    } catch (error) {
        console.error('❌ MCP Connection Test failed with error:', error.message);
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    main();
}

module.exports = MCPConnectionTest;