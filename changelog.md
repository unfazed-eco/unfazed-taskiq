v0.0.5
=====
• Add early return guard in setup() method when already initialized

v0.0.4
=====

• Multi-broker architecture: Refactored TaskiqAgent to support multiple brokers and schedulers with dictionary-based configuration
• Database-backed scheduling: Added TortoiseScheduleSource for MySQL-based task scheduling with CRUD operations and persistence
• CLI enhancements: Implemented SchedulerCMD and WorkerCMD with multi-scheduler support and Sentry integration
• Task decorator system: Added @task decorator with automatic registration, broker selection, and parameter extraction
• Exception handling: Created middleware with Sentry integration for comprehensive error tracking and logging
• Comprehensive test suite: Added extensive unit tests covering all new components with 95%+ coverage
• Configuration updates: Restructured settings to support multi-broker configurations and added MySQL dependencies
• Documentation overhaul: Complete rewrite with quick start guide, multi-broker examples, and scheduling instructions


v0.0.2
=====

- solve [issue #2](https://github.com/unfazed-eco/unfazed-taskiq/issues/2) failed to use `taskiq` cli command

