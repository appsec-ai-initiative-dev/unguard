#!/usr/bin/env node

/*
 * Basic validation test for the MCP connection test script
 * This ensures the script structure and logic are correct
 */

const MCPConnectionTest = require('./test-connections.js');

async function validateTestStructure() {
    console.log('🔍 Validating MCP Connection Test Structure...');
    
    const test = new MCPConnectionTest();
    
    // Validate service configuration
    if (!test.services || test.services.length === 0) {
        throw new Error('No services configured');
    }
    
    console.log(`✅ Found ${test.services.length} services configured`);
    
    // Validate each service has required fields
    for (const service of test.services) {
        if (!service.name) throw new Error(`Service missing name: ${JSON.stringify(service)}`);
        if (!service.url) throw new Error(`Service missing URL: ${service.name}`);
        if (!service.description) throw new Error(`Service missing description: ${service.name}`);
        
        console.log(`✅ ${service.name}: ${service.url}`);
    }
    
    // Validate timeout configuration
    if (!test.timeout || test.timeout <= 0) {
        throw new Error('Invalid timeout configuration');
    }
    
    console.log(`✅ Timeout configured: ${test.timeout}ms`);
    
    // Test URL parsing
    for (const service of test.services) {
        try {
            new URL(service.url);
        } catch (error) {
            throw new Error(`Invalid URL for ${service.name}: ${service.url}`);
        }
    }
    
    console.log('✅ All URLs are valid');
    
    console.log('🎉 MCP Connection Test structure validation passed!');
    return true;
}

// Run validation if called directly
if (require.main === module) {
    validateTestStructure()
        .then(() => process.exit(0))
        .catch(error => {
            console.error('❌ Validation failed:', error.message);
            process.exit(1);
        });
}

module.exports = validateTestStructure;