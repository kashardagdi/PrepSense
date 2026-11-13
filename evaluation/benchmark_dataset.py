"""
PrepSense - Evaluation Benchmark Dataset.

Contains 20 curated real-world candidate profiles and matching job descriptions
across different experience levels, specializations, and company requirements.
"""

from __future__ import annotations

BENCHMARK_SCENARIOS = [
    {
        "id": "sde_intern_amazon",
        "role": "Software Development Engineer (SDE) Intern",
        "company": "Amazon",
        "job_description": """
Amazon is looking for software development engineer interns.
Key qualifications:
- Solid understanding of Computer Science fundamentals, Object-Oriented Design (OOD), Data Structures and Algorithms.
- Programming proficiency in at least one modern language: Java, C++, Python, or C#.
- Experience with relational databases and SQL queries.
- Familiarity with cloud technologies (AWS preferred) and containerization using Docker.
- Strong problem-solving, debugging skills and ability to communicate effectively.
        """,
        "resume_text": """
Kashan - Computer Science Student
Education: BS in Computer Science, Expected 2027.
Skills: Python, C++, Data Structures, Algorithms, SQL, Git, Linux.
Projects:
1. Distributed Task Scheduler: Built with Python and Redis to handle asynchronous background jobs. Implemented custom priority queues.
2. E-commerce REST API: Developed backend endpoints using FastAPI and SQLite. Integrated JWT authentication.
Activities: Competitive programming on LeetCode (solved 350+ DSA problems).
        """,
        "expected_skills": ["Python", "C++", "SQL", "Docker", "AWS", "Data Structures"],
    },
    {
        "id": "backend_engineer_stripe",
        "role": "Backend Engineer",
        "company": "Stripe",
        "job_description": """
Stripe builds economic infrastructure for the internet.
Requirements:
- 2+ years backend development experience with Go, Python, or Ruby.
- Deep expertise in distributed systems, RESTful APIs, and microservices architecture.
- Extensive experience with PostgreSQL, schema migration, and transaction management.
- Hands-on experience with Docker, Kubernetes, and CI/CD deployment pipelines.
- Focus on high availability, zero-downtime deployments, and payment security standards.
        """,
        "resume_text": """
Alex Chen - Software Engineer
Experience:
Software Engineer at Fintech Startup (2 years):
- Designed and maintained payment integration microservices using Python, FastAPI, and PostgreSQL.
- Optimized slow SQL queries with indexing and connection pooling, dropping p99 latency by 45%.
- Packaged services into Docker containers and configured GitHub Actions workflows for continuous integration.
Skills: Python, PostgreSQL, REST APIs, Docker, Git, Redis.
        """,
        "expected_skills": ["Python", "PostgreSQL", "Docker", "Kubernetes", "Go"],
    },
    {
        "id": "frontend_developer_airbnb",
        "role": "Frontend Software Engineer",
        "company": "Airbnb",
        "job_description": """
Join Airbnb as a Frontend Engineer crafting delightful guest and host experiences.
Requirements:
- Strong command of modern JavaScript (ES6+), TypeScript, and HTML/CSS.
- Extensive production experience with React, state management (Redux/Zustand), and React Hooks.
- Experience with web performance profiling, SSR (Next.js), and responsive design.
- Familiarity with testing frameworks such as Jest, React Testing Library, and Cypress.
- Collaborative mindset and attention to accessible UI/UX.
        """,
        "resume_text": """
Sarah Miller - Frontend Specialist
Experience:
Frontend Developer (1.5 years):
- Developed interactive web interfaces using React, TypeScript, and Tailwind CSS.
- Built reusable component library adhering to WCAG accessibility standards.
- Wrote automated unit tests with Jest and React Testing Library.
Skills: TypeScript, JavaScript, React, Tailwind CSS, Jest, Git, HTML5, CSS3.
        """,
        "expected_skills": ["TypeScript", "React", "Next.js", "Jest", "CSS"],
    },
    {
        "id": "ml_engineer_meta",
        "role": "Machine Learning Engineer",
        "company": "Meta",
        "job_description": """
Meta is hiring Machine Learning Engineers to build recommender systems and deep learning models.
Requirements:
- Strong programming skills in Python and C++.
- Hands-on experience with deep learning frameworks: PyTorch or TensorFlow.
- Experience training, fine-tuning, and evaluating models on large-scale datasets.
- Understanding of distributed model training, CUDA, and model serving (Triton / ONNX).
- Background in mathematical foundations (linear algebra, probability, calculus).
        """,
        "resume_text": """
David Kim - AI / ML Researcher
Education: M.S. in Artificial Intelligence
Experience:
ML Intern at Vision Labs:
- Trained computer vision models using PyTorch for object detection.
- Utilized Pandas, NumPy, and Scikit-learn for dataset preprocessing and feature extraction.
- Profiled model inference on NVIDIA GPUs.
Skills: Python, PyTorch, Scikit-learn, Pandas, NumPy, Git, Linux.
        """,
        "expected_skills": ["Python", "PyTorch", "C++", "CUDA", "Pandas"],
    },
    {
        "id": "devops_engineer_netflix",
        "role": "Senior Cloud Infrastructure Engineer",
        "company": "Netflix",
        "job_description": """
Manage and evolve Netflix's cloud infrastructure at scale.
Requirements:
- Deep expertise in AWS cloud services (EC2, S3, RDS, IAM, VPC, CloudWatch).
- Strong experience with Infrastructure as Code (Terraform or CloudFormation).
- Production container orchestration with Kubernetes and service mesh.
- Proficient in scripting with Python or Bash for system automation.
- Experience setting up monitoring, Prometheus, Grafana, and incident response.
        """,
        "resume_text": """
Priya Sharma - Cloud Systems Engineer
Experience:
DevOps Engineer (3 years):
- Automated cloud infrastructure provisioning using Terraform across AWS environments.
- Managed multi-node Kubernetes clusters and deployed microservices with Helm charts.
- Scripted operational automation and database backup jobs using Python and Bash.
- Configured Grafana dashboards and Prometheus alerts for system health monitoring.
Skills: AWS, Terraform, Kubernetes, Docker, Python, Bash, Prometheus, Grafana.
        """,
        "expected_skills": ["AWS", "Terraform", "Kubernetes", "Python", "Docker"],
    },
    {
        "id": "fullstack_engineer_startup",
        "role": "Full Stack Engineer",
        "company": "Y Combinator Startup",
        "job_description": """
Fast-paced startup seeking full-stack engineers to build customer-facing applications.
Requirements:
- Proficiency with TypeScript across frontend (React / Next.js) and backend (Node.js / Express).
- Experience with relational or NoSQL databases (MongoDB, PostgreSQL).
- Experience integrating third-party APIs (Stripe, Twilio, OpenAI).
- Agile product development, rapid iteration, and ownership.
        """,
        "resume_text": """
Leo Torres - Full Stack Developer
Experience:
Full Stack Developer at Digital Agency (2 years):
- Built web apps using TypeScript, Node.js, Express, and MongoDB.
- Created interactive client portals with React and Next.js.
- Integrated Stripe payment processing and OAuth authentication.
Skills: TypeScript, Node.js, React, Next.js, Express, MongoDB, Git.
        """,
        "expected_skills": ["TypeScript", "Node.js", "React", "PostgreSQL", "MongoDB"],
    },
    {
        "id": "data_engineer_uber",
        "role": "Data Engineer",
        "company": "Uber",
        "job_description": """
Design and maintain Uber's real-time and batch data pipelines.
Requirements:
- Strong experience in Python, SQL, and distributed computing frameworks (Apache Spark, PySpark).
- Experience with workflow orchestration (Airflow) and data warehousing (Snowflake / BigQuery).
- Familiarity with Kafka or real-time event streaming architectures.
- Experience optimizing ETL pipelines for terabyte-scale data lakes.
        """,
        "resume_text": """
Rahul Verma - Data Engineer
Experience:
Data Engineer (2 years):
- Built automated batch ETL pipelines using Python and Apache Airflow.
- Wrote complex SQL transformations and stored procedures in PostgreSQL.
- Conducted data analysis and pipeline validations using PySpark.
Skills: Python, SQL, Apache Airflow, PySpark, PostgreSQL, Docker, Git.
        """,
        "expected_skills": ["Python", "SQL", "Apache Spark", "Airflow", "Kafka"],
    },
    {
        "id": "mobile_developer_spotify",
        "role": "Mobile Engineer (Android)",
        "company": "Spotify",
        "job_description": """
Deliver audio experiences to millions of Spotify listeners worldwide.
Requirements:
- Proficiency in modern Android development with Kotlin and Java.
- Experience with Jetpack Compose, Coroutines, Flow, and MVVM architecture.
- Understanding of audio playback, background services, and memory optimization on Android.
- Experience with automated UI and unit testing (Espresso, JUnit).
        """,
        "resume_text": """
Daniel Garcia - Android Developer
Experience:
Android Developer (1.5 years):
- Developed consumer Android applications using Kotlin and Jetpack Compose.
- Utilized Kotlin Coroutines for asynchronous network requests and Room database storage.
- Implemented unit tests using JUnit and Mockito.
Skills: Kotlin, Java, Android SDK, Jetpack Compose, Coroutines, Git.
        """,
        "expected_skills": ["Kotlin", "Android SDK", "Jetpack Compose", "Java", "Espresso"],
    },
    {
        "id": "qa_automation_microsoft",
        "role": "Software Development Engineer in Test (SDET)",
        "company": "Microsoft",
        "job_description": """
Ensure software quality and test scalability for enterprise cloud solutions.
Requirements:
- Strong coding skills in Python, C#, or Java.
- Extensive experience designing test automation frameworks with Selenium, Playwright, or Cypress.
- Experience with API test automation (REST Assured, Postman, PyTest).
- Familiarity with CI/CD integration using Azure DevOps or GitHub Actions.
- Solid knowledge of test strategy, regression, and performance testing.
        """,
        "resume_text": """
Emma Watson - QA Automation Engineer
Experience:
SDET (2 years):
- Built end-to-end web test automation suites using Python and Selenium WebDriver.
- Automated REST API testing using PyTest and Postman.
- Configured automated test runs in GitHub Actions CI pipelines on pull requests.
Skills: Python, Selenium, PyTest, Git, Postman, CI/CD, SQL.
        """,
        "expected_skills": ["Python", "Selenium", "Cypress", "PyTest", "CI/CD"],
    },
    {
        "id": "systems_engineer_cloudflare",
        "role": "Systems Software Engineer",
        "company": "Cloudflare",
        "job_description": """
Build network edge services and low-latency infrastructure.
Requirements:
- Proficiency in systems programming with C, C++, or Rust.
- Deep understanding of Linux OS internals, system calls, sockets, and memory management.
- Strong knowledge of networking protocols (TCP/IP, HTTP/2, DNS, TLS).
- Experience with high-performance concurrent programming and performance profiling.
        """,
        "resume_text": """
Vikram Patel - Systems Programmer
Experience:
Systems Developer:
- Built a multi-threaded network proxy in C++ using epoll and non-blocking sockets.
- Debugged kernel socket buffers and memory leaks using valgrind and gdb.
- Solid understanding of TCP/IP stack and Linux process management.
Skills: C++, C, Linux, Concurrency, Git, GDB, Socket Programming.
        """,
        "expected_skills": ["C++", "C", "Rust", "Linux", "Networking"],
    },
    {
        "id": "security_engineer_google",
        "role": "Application Security Engineer",
        "company": "Google",
        "job_description": """
Help secure Google products and infrastructure against modern threats.
Requirements:
- Strong programming skills in Python, Go, or Java.
- Deep knowledge of application security vulnerabilities (OWASP Top 10), authentication, and cryptography.
- Experience performing security code reviews, threat modeling, and penetration testing.
- Understanding of web security mechanisms (CSP, CORS, OAuth, TLS).
        """,
        "resume_text": """
Maya Lin - Security Specialist
Experience:
AppSec Engineer (2 years):
- Conducted static and dynamic code security assessments for Python and Go applications.
- Remediated OWASP vulnerabilities including SQL injection, XSS, and SSRF.
- Automated security scanning in CI/CD pipelines using open-source tools.
Skills: Python, Go, AppSec, OWASP, Penetration Testing, Linux, Git.
        """,
        "expected_skills": ["Python", "Go", "OWASP", "Cryptography", "AppSec"],
    },
    {
        "id": "site_reliability_engineer_linkedin",
        "role": "Site Reliability Engineer (SRE)",
        "company": "LinkedIn",
        "job_description": """
Ensure LinkedIn services are highly reliable, scalable, and resilient.
Requirements:
- Strong scripting and automation skills in Python, Go, or Bash.
- Deep operational experience with Linux systems, networking, and distributed systems.
- Experience with telemetry, distributed tracing, and monitoring tools.
- Understanding of SLIs, SLOs, error budgets, and blameless post-mortem culture.
        """,
        "resume_text": """
Kevin Zhao - Site Reliability Engineer
Experience:
SRE (2 years):
- Maintained 99.95% service uptime across critical microservices using Python monitoring scripts.
- Implemented alerting rules, Prometheus metrics, and automated alert response playbooks.
- Conducted root-cause investigations and blameless post-mortems for production incidents.
Skills: Python, Linux, Prometheus, Grafana, Docker, Bash, Git.
        """,
        "expected_skills": ["Python", "Go", "Linux", "SLO", "Prometheus"],
    },
    {
        "id": "ios_developer_apple",
        "role": "iOS Software Engineer",
        "company": "Apple",
        "job_description": """
Design and build next-generation applications for iOS.
Requirements:
- Deep expertise in Swift, Objective-C, and Apple frameworks (UIKit, SwiftUI, CoreData).
- Understanding of iOS app architecture (MVVM, Clean Architecture) and memory management (ARC).
- Experience with multithreading using Grand Central Dispatch (GCD) and Swift Concurrency.
- Passion for smooth animations, fluid gesture interactions, and battery efficiency.
        """,
        "resume_text": """
Chloe Bennett - iOS Engineer
Experience:
iOS Developer (2 years):
- Developed and released native iOS applications on the App Store using Swift and SwiftUI.
- Managed local persistent storage with CoreData and integrated REST APIs.
- Handled concurrency using Swift async/await and GCD.
Skills: Swift, SwiftUI, UIKit, CoreData, Xcode, Git, REST APIs.
        """,
        "expected_skills": ["Swift", "SwiftUI", "UIKit", "Objective-C", "CoreData"],
    },
    {
        "id": "database_admin_oracle",
        "role": "Database Administrator / Engineer",
        "company": "Oracle",
        "job_description": """
Administer enterprise database platforms and mission-critical clusters.
Requirements:
- Expertise in relational database architecture, SQL, and query optimization.
- Experience with database backup and recovery (RMAN), high-availability (Data Guard), and replication.
- Proficient in performance tuning, explain plans, indexing strategies, and buffer cache management.
- Linux administration and shell scripting proficiency.
        """,
        "resume_text": """
Suresh Nair - Database Specialist
Experience:
Database Administrator:
- Managed multi-terabyte Oracle and PostgreSQL database instances.
- Optimized query execution plans and eliminated deadlock bottlenecks.
- Wrote Bash and SQL automation scripts for daily backups and health checks.
Skills: SQL, PostgreSQL, Oracle, Linux, Bash, Performance Tuning.
        """,
        "expected_skills": ["SQL", "PostgreSQL", "Oracle", "Linux", "Performance Tuning"],
    },
    {
        "id": "embedded_engineer_tesla",
        "role": "Firmware & Embedded Software Engineer",
        "company": "Tesla",
        "job_description": """
Develop real-time firmware for vehicle control and battery management systems.
Requirements:
- High proficiency in C and C++ for bare-metal and RTOS environments (FreeRTOS).
- Experience with hardware communication protocols: CAN, SPI, I2C, UART.
- Ability to debug hardware interfaces using oscilloscopes and logic analyzers.
- Understanding of low-power design, memory constraints, and safety-critical standards.
        """,
        "resume_text": """
Lucas Silva - Firmware Developer
Experience:
Embedded Engineer:
- Developed C/C++ firmware for ARM Cortex-M microcontrollers using FreeRTOS.
- Implemented SPI and CAN bus communication drivers for sensor data acquisition.
- Debugged hardware boards using logic analyzers and JTAG/SWD probes.
Skills: C, C++, FreeRTOS, CAN, SPI, ARM, Git, Embedded Linux.
        """,
        "expected_skills": ["C", "C++", "FreeRTOS", "CAN", "SPI"],
    },
    {
        "id": "cloud_architect_ibm",
        "role": "Cloud Solutions Architect",
        "company": "IBM",
        "job_description": """
Design enterprise hybrid-cloud solutions for global clients.
Requirements:
- Deep knowledge of cloud architecture patterns, microservices, and hybrid cloud migrations.
- Experience with Red Hat OpenShift, Kubernetes, and container security.
- Understanding of enterprise integration, API gateways, and multi-tenant data architectures.
- Strong client-facing communication and architectural diagramming skills.
        """,
        "resume_text": """
Anita Roy - Cloud Consultant
Experience:
Solutions Engineer (3 years):
- Designed containerized cloud migration blueprints using Red Hat OpenShift and Kubernetes.
- Advised clients on cloud security, network topology, and disaster recovery architectures.
- Automated deployment configurations using Ansible and Docker.
Skills: Kubernetes, OpenShift, Docker, Cloud Architecture, Ansible, Git.
        """,
        "expected_skills": ["Kubernetes", "OpenShift", "Cloud Architecture", "Docker", "Ansible"],
    },
    {
        "id": "blockchain_engineer_coinbase",
        "role": "Blockchain Protocol Engineer",
        "company": "Coinbase",
        "job_description": """
Build secure crypto exchange and decentralized protocol integrations.
Requirements:
- Strong proficiency in Go, Rust, or C++.
- Understanding of cryptography, consensus algorithms, and blockchain node operations.
- Experience with smart contract development or Ethereum/Bitcoin RPC APIs.
- Passion for security, formal verification, and distributed consensus.
        """,
        "resume_text": """
Ethan Wright - Blockchain Developer
Experience:
Web3 Developer:
- Built decentralized backend services using Go and Ethereum JSON-RPC nodes.
- Wrote and tested smart contracts in Solidity with Hardhat and Foundry.
- Implemented cryptographic signature verification and key management flows.
Skills: Go, Solidity, Ethereum, Cryptography, Git, Linux.
        """,
        "expected_skills": ["Go", "Solidity", "Rust", "Cryptography", "Ethereum"],
    },
    {
        "id": "game_developer_epic",
        "role": "Gameplay Programmer",
        "company": "Epic Games",
        "job_description": """
Create gameplay systems and multiplayer features using Unreal Engine.
Requirements:
- Exceptional C++ programming skills, math (3D vector math, linear algebra, physics).
- Hands-on experience developing in Unreal Engine 5 (UE5).
- Experience with multiplayer client-server network replication and state sync.
- Strong performance profiling and memory optimization skills.
        """,
        "resume_text": """
Tom Rogers - Game Programmer
Experience:
Gameplay Programmer:
- Developed multiplayer game mechanics in C++ and Blueprints within Unreal Engine 5.
- Implemented client-side prediction and server replication for character abilities.
- Profiled frame times and memory allocations using Unreal Insights.
Skills: C++, Unreal Engine, 3D Math, Multiplayer Networking, Git.
        """,
        "expected_skills": ["C++", "Unreal Engine", "3D Math", "Networking", "Physics"],
    },
    {
        "id": "nlp_engineer_openai",
        "role": "NLP / AI Research Engineer",
        "company": "OpenAI",
        "job_description": """
Advance the state of language modeling and agentic AI systems.
Requirements:
- Mastery of Python and deep learning frameworks (PyTorch, JAX).
- Extensive experience with Transformer architectures, attention mechanisms, and LLM fine-tuning.
- Experience with RLHF, tokenization, and synthetic data generation.
- Strong engineering discipline for scaling distributed training clusters.
        """,
        "resume_text": """
Zainab Farooq - NLP Engineer
Experience:
AI Engineer:
- Fine-tuned open-source Transformer models using PyTorch and Hugging Face Transformers.
- Built retrieval-augmented generation (RAG) pipelines with vector embeddings and LangChain.
- Preprocessed large text corpora and implemented evaluation benchmarks.
Skills: Python, PyTorch, Transformers, Hugging Face, NLP, Git.
        """,
        "expected_skills": ["Python", "PyTorch", "Transformers", "NLP", "JAX"],
    },
    {
        "id": "product_manager_technical_google",
        "role": "Technical Product Manager (Cloud)",
        "company": "Google",
        "job_description": """
Lead product strategy and execution for developer-facing cloud platforms.
Requirements:
- Bachelor's degree in Computer Science or equivalent practical technical experience.
- Experience translating complex developer requirements into actionable product roadmaps.
- Strong analytical skills, user research, and data-driven decision making.
- Familiarity with cloud services, API design, and modern developer workflows.
        """,
        "resume_text": """
Marcus Brody - Technical Product Manager
Experience:
Associate Product Manager (2 years):
- Defined product specifications and roadmap for developer API platforms used by 15k+ devs.
- Analyzed product telemetry and conducted 30+ developer interviews to prioritize features.
- Collaborated with engineering teams to scope architectural trade-offs and release schedules.
Skills: Product Management, Agile, API Design, Data Analysis, SQL, Jira.
        """,
        "expected_skills": ["Product Management", "API Design", "SQL", "Cloud", "Agile"],
    },
]
