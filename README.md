# Interactive Devices & Physical Computing

**Pablo Peñalba Lázaro | Cornell Tech | Fall 2026**

A growing portfolio of hands-on projects exploring the intersection of **embedded systems, physical computing, human–computer interaction, and intelligent devices**.

Developed as part of *INFO 5345 – Designing Interactive Devices* at Cornell Tech, this repository documents my progression from foundational electronics and hardware prototyping to integrated systems that sense their environments and respond through physical interactions.

The broader objective is to understand how hardware and software work together to enable increasingly intelligent, context-aware, and autonomous physical devices.

## Technical Focus

**Embedded Computing & Hardware Integration**
- Raspberry Pi 5 and microcontrollers
- GPIO, I²C, and peripheral communication
- Sensors, actuators, displays, and interactive components
- Hardware integration and troubleshooting

**Sensing, Actuation & Interaction**
- Proximity, distance, motion, and gesture sensing
- Servo motor control and physical actuation
- Sensor calibration and signal interpretation
- Event-driven programming and real-time interactions

**Software & Systems**
- Python programming
- Hardware–software integration
- State-based interaction logic
- Experimental testing, debugging, and performance evaluation
- Exploration of local AI inference on embedded systems

## Projects & Labs

| Lab | Focus | Documentation |
|---|---|---|
| Lab 1 – Recreating the Masters | Foundations of interactive device design | [View Lab](Lab%201/) |
| Lab 2 – The Clock of Pi | Interactive prototyping and embedded computing | [View Lab](Lab%202/) |
| Lab 3 – Chatterboxes | Voice-based interaction and conversational interfaces | [View Lab](Lab%203/) |
| Lab 4 – Ph-UI!!! | Sensor integration, physical actuation, and interactive prototyping | [View Lab](Lab%204/) |
| Lab 5 – Observant Systems | Sensing, machine perception, and local AI experimentation | [View Lab](Lab%205/) |
| Lab 6 – Little Interactions Everywhere | Upcoming | — |
| Final Project | Upcoming | — |

## Featured Prototype: Thirst Nudge

**Lab 4 – Sensor-Driven Physical Interaction**

Designed and implemented an interactive device that detects the presence and movement of a drinking mug and provides a physical reminder through a servo-actuated flag.

The prototype integrates:

- Raspberry Pi 5 for processing and control
- VCNL4040 proximity sensor for detecting mug placement and removal
- Servo motor for physical feedback
- Python-based state logic, timing, and actuation

**Engineering highlights:**
- Experimentally calibrated proximity detection thresholds.
- Implemented consecutive-reading validation to reduce false detections.
- Integrated sensor inputs with timed servo movements.
- Improved reliability through hardware troubleshooting and software iteration.
- Measured and documented system behavior and response times.

The project demonstrates a complete **sense–process–act loop**, connecting physical inputs to programmed decisions and mechanical outputs.

[Explore the prototype, code, and documentation](Lab%204/)

## Development Approach

Across these projects, I follow an iterative engineering process:

1. **Explore:** Understand the components, interfaces, and technical constraints.
2. **Prototype:** Build and test individual hardware and software functions.
3. **Integrate:** Connect sensing, processing, and actuation into functioning systems.
4. **Validate:** Collect measurements, identify limitations, and troubleshoot unexpected behavior.
5. **Iterate:** Refine the system based on experimental results and user interaction.

Each lab includes documentation of the implementation, technical challenges, design decisions, and lessons learned.

## Looking Ahead

I'm particularly interested in **Physical AI and edge intelligence**—systems that combine local perception, embedded computing, autonomous decision-making, and natural human interaction.

Future work will explore how machine learning and multimodal AI can extend these foundations toward physical devices capable of interpreting their surroundings and responding intelligently.

---

*This repository is an ongoing learning and prototyping portfolio developed at Cornell Tech. Projects and documentation will continue to evolve throughout the semester.*


