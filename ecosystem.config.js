// PM2 Ecosystem Configuration
//
// Usage:
//   pm2 start ecosystem.config.js
//   pm2 start ecosystem.config.js --only crazy-trade-bot
//   pm2 start ecosystem.config.js --only crazy-trade-api
//   pm2 start ecosystem.config.js --only crazy-trade-monitor
//
// Run bot + API + system monitor together:
//   pm2 start ecosystem.config.js
//
// Monitor:
//   pm2 status
//   pm2 logs crazy-trade-bot
//   pm2 logs crazy-trade-monitor
//   pm2 monit
//
// Stop:
//   pm2 stop all
//   pm2 delete all
//
// Note: health_status.json is written by crazy-trade-monitor; the bot reads it
// each loop to enable low_power_mode (RSI-only indicators) when CPU/temp is high.

module.exports = {
  apps: [
    {
      name: 'crazy-trade-monitor',
      script: 'system_monitor.py',
      interpreter: 'python3',
      cwd: __dirname,

      env: {
        PYTHONUNBUFFERED: '1',
      },

      log_file: './logs/pm2-monitor.log',
      out_file: './logs/pm2-monitor-out.log',
      error_file: './logs/pm2-monitor-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,

      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '100M',

      restart_delay: 3000,
      max_restarts: 10,
      min_uptime: '5s',

      kill_timeout: 5000,
    },
    {
      name: 'crazy-trade-bot',
      script: 'main.py',
      interpreter: 'python3',
      cwd: __dirname,
      
      // Environment
      env: {
        PYTHONUNBUFFERED: '1',  // Ensure logs are flushed immediately
      },
      
      // Logging
      log_file: './logs/pm2-bot.log',
      out_file: './logs/pm2-bot-out.log',
      error_file: './logs/pm2-bot-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      
      // Process management
      instances: 1,              // Single instance (trading bot should not be parallelized)
      autorestart: true,         // Auto-restart on crash
      watch: false,              // Don't watch for file changes
      max_memory_restart: '500M', // Restart if memory exceeds 500MB
      
      // Restart behavior
      restart_delay: 5000,       // Wait 5 seconds before restart
      max_restarts: 10,          // Max restarts in a row
      min_uptime: '30s',         // Consider started after 30 seconds
      
      // Graceful shutdown
      kill_timeout: 10000,       // Wait 10 seconds for graceful shutdown
      listen_timeout: 3000,
      
      // Cron restart (optional - restart daily at 4am to clear memory)
      // cron_restart: '0 4 * * *',
    },
    
    {
      name: 'crazy-trade-api',
      script: 'api_server.py',
      interpreter: 'python3',
      cwd: __dirname,
      
      // Environment
      env: {
        PYTHONUNBUFFERED: '1',
        PORT: '8080',
      },
      
      // Logging
      log_file: './logs/pm2-api.log',
      out_file: './logs/pm2-api-out.log',
      error_file: './logs/pm2-api-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      
      // Process management
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      
      // Restart behavior
      restart_delay: 3000,
      max_restarts: 10,
      min_uptime: '10s',
      
      // Graceful shutdown
      kill_timeout: 5000,
    }
  ]
};
