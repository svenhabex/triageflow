# LLM Request Monitoring & Optimization Guide

This document outlines the LLM monitoring system and optimization strategies implemented to track and reduce LLM API usage in the TriageFlow application.

## 🔍 Current LLM Usage Analysis

### Original Architecture Issues

The original implementation had several inefficiencies:

1. **Multiple LLM Calls per Agent**:

   - Intake Agent: 2 separate calls (conversation parsing + tool coordination)
   - Triage Agent: 1 call (assessment)
   - Coordinator Agent: 1+ calls (tool calling cycles)

2. **Retry Loops**: Up to 5 iterations per agent with tool calling
3. **No Usage Tracking**: No visibility into request counts or costs
4. **Redundant Operations**: Separate parsing and analysis steps

### Typical Request Flow (Original)

```
Session Start
├── Intake Agent
│   ├── LLM Call 1: Parse conversation → IntakeConversationInfo
│   └── LLM Call 2: Analyze + tool calling (1-5 iterations)
├── Triage Agent
│   └── LLM Call 3: Assess patient → TriageInformation
└── Coordinator Agent
    └── LLM Call 4+: Staff coordination (1-5 iterations)

Total: 4-13 LLM requests per session
```

## 📊 Monitoring System

### Core Components

#### 1. LLMMonitor (`src/core/llm_monitor.py`)

- **Request Tracking**: Automatic logging of all LLM requests
- **Cost Estimation**: Real-time cost calculation using Gemini pricing
- **Performance Metrics**: Duration, token usage, success rates
- **Pattern Analysis**: Identifies optimization opportunities

#### 2. ProductionMonitor (`src/core/monitoring_utils.py`)

- **Session Analytics**: Per-session usage summaries
- **Efficiency Scoring**: 0-100 efficiency score calculation
- **Alert System**: Cost threshold monitoring
- **Export Capabilities**: JSON/CSV data export

#### 3. Tracking Decorator

```python
@track_llm_request("agent_name", "method_name", "request_type")
async def llm_method(self, state: WorkflowState):
    # Your LLM call here
    pass
```

### Usage Example

```python
from src.core.llm_monitor import llm_monitor
from src.core.monitoring_utils import ProductionMonitor

# Get session statistics
stats = llm_monitor.get_stats("session_123")
print(f"Total requests: {stats.total_requests}")
print(f"Estimated cost: ${stats.total_cost_estimate:.4f}")

# Generate optimization report
report = ProductionMonitor.get_optimization_report("session_123")
print(report)
```

## ⚡ Optimization Strategies

### 1. Optimized Intake Agent (`src/agents/optimized_intake.py`)

**Key Improvements**:

- **Combined Operations**: Single LLM call instead of 2 separate calls
- **Reduced Iterations**: Max 3 iterations instead of 5
- **Smart Tool Usage**: Only call tools when patient names are mentioned
- **Efficient Prompting**: More focused system prompts

**Request Reduction**: ~50% fewer LLM calls for intake processing

### 2. Enhanced Prompting

- **Structured Outputs**: Use Pydantic models for consistent parsing
- **Context Optimization**: JSON context instead of full message history
- **Clear Instructions**: Reduce ambiguity and improve first-time success

### 3. Retry Optimization

- **Lower Max Iterations**: Reduced from 5 to 3 iterations
- **Early Exit Conditions**: Stop when sufficient data is available
- **Error Handling**: Better error messages to reduce retry loops

## 📈 Testing & Comparison

### Running the Test Suite

```bash
cd apps/backend
python test_llm_monitoring.py
```

### Expected Results

```
🔍 ORIGINAL INTAKE AGENT:
  Total LLM Requests: 3-4
  Estimated Cost: $0.0080-0.0120

⚡ OPTIMIZED INTAKE AGENT:
  Total LLM Requests: 2-3
  Estimated Cost: $0.0050-0.0080

💰 OPTIMIZATION SAVINGS:
  Request Reduction: 25-50%
  Cost Reduction: 25-40%
```

## 🚨 Production Monitoring

### Environment Variables

```bash
# Enable/disable monitoring
LLM_MONITORING_ENABLED=true

# Your Gemini API key
GEMINI_API_KEY=your_api_key_here
```

### Integration with Workflow Service

```python
from src.core.monitoring_utils import add_monitoring_to_workflow_response

# In your workflow completion handler
response_data = {"workflow_result": result}
response_with_monitoring = add_monitoring_to_workflow_response(
    session_id, response_data
)
```

### Cost Alerts

```python
from src.core.monitoring_utils import ProductionMonitor

# Check if session exceeded cost threshold
alert = ProductionMonitor.check_cost_threshold(
    session_id="session_123",
    threshold_usd=0.10
)

if alert["threshold_exceeded"]:
    print(f"⚠️ Cost alert: ${alert['current_cost']:.4f}")
```

## 💡 Additional Optimization Opportunities

### 1. Caching Strategy

```python
# Patient record caching
patient_cache = {}

def get_cached_patient(patient_id: str):
    if patient_id in patient_cache:
        return patient_cache[patient_id]

    patient = fetch_from_database(patient_id)
    patient_cache[patient_id] = patient
    return patient
```

### 2. Model Selection Optimization

```python
# Use different models for different tasks
MODELS = {
    "simple_parsing": "gemini-1.5-flash",      # Cheaper for basic tasks
    "complex_reasoning": "gemini-1.5-pro",     # More capable for complex logic
    "structured_output": "gemini-1.5-flash"   # Good balance for structured tasks
}
```

### 3. Batch Processing

```python
# Process multiple similar requests together
async def batch_triage_assessments(patients: list[PatientData]):
    # Single LLM call for multiple patients
    batch_prompt = create_batch_triage_prompt(patients)
    return await model.ainvoke(batch_prompt)
```

### 4. Prompt Optimization

- **Shorter Prompts**: Remove unnecessary instructions
- **Examples**: Provide clear examples for better first-time success
- **Temperature Tuning**: Lower temperature (0.3-0.7) for more consistent outputs

## 📊 Monitoring Dashboard Ideas

### Key Metrics to Track

1. **Request Volume**: Total requests per hour/day
2. **Cost Tracking**: Daily/monthly spend
3. **Success Rates**: Failed vs successful requests
4. **Response Times**: Average LLM response duration
5. **Agent Efficiency**: Requests per successful workflow completion

### Alert Thresholds

- **High Cost**: >$1.00 per day
- **High Retry Rate**: >15% retries
- **Slow Responses**: >5 seconds average
- **High Failure Rate**: >10% failures

## 🔧 Implementation Checklist

### Phase 1: Monitoring (✅ Complete)

- [x] LLM request tracking system
- [x] Cost estimation and monitoring
- [x] Performance metrics collection
- [x] Optimization recommendations engine

### Phase 2: Basic Optimization (✅ Complete)

- [x] Optimized intake agent implementation
- [x] Reduced retry iterations
- [x] Smart tool usage patterns
- [x] Performance comparison testing

### Phase 3: Advanced Optimization (🚧 Recommended)

- [ ] Patient record caching
- [ ] Staff lookup caching
- [ ] Model selection optimization
- [ ] Batch processing capabilities
- [ ] Production monitoring dashboard

### Phase 4: Production Integration (🚧 Recommended)

- [ ] Real-time cost alerts
- [ ] Daily/weekly usage reports
- [ ] Integration with logging infrastructure
- [ ] Performance SLA monitoring

## 🎯 Expected Benefits

### Immediate (Phase 1-2)

- **25-50% reduction** in LLM requests
- **Real-time visibility** into usage patterns
- **Cost tracking** and budget management
- **Performance insights** for optimization

### Long-term (Phase 3-4)

- **60-80% cost reduction** with caching
- **Improved response times** with optimization
- **Predictable costs** with monitoring
- **Scalable architecture** for growth

## 📝 Usage Guidelines

### Best Practices

1. **Monitor First**: Always check monitoring data before optimizing
2. **Test Changes**: Use the test suite to validate optimizations
3. **Gradual Rollout**: Implement optimizations incrementally
4. **Track Impact**: Measure the effect of each optimization

### Common Pitfalls

1. **Over-optimization**: Don't sacrifice accuracy for cost savings
2. **Ignoring Errors**: High retry rates indicate prompt/logic issues
3. **Cache Invalidation**: Ensure cached data stays fresh
4. **Missing Edge Cases**: Test with various conversation types

## 🤝 Contributing

When adding new LLM functionality:

1. **Add Monitoring**: Use `@track_llm_request` decorator
2. **Test Impact**: Run comparison tests
3. **Update Documentation**: Document new patterns
4. **Consider Optimization**: Look for combining or caching opportunities

Example:

```python
@track_llm_request("new_agent", "new_method", "structured")
async def new_llm_method(self, state: WorkflowState):
    # Your new LLM functionality
    pass
```

This monitoring and optimization system provides comprehensive visibility into LLM usage while offering concrete strategies to reduce costs and improve performance.
