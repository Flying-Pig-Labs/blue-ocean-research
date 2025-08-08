FROM jupyter/scipy-notebook:python-3.11

USER root

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY *.py ./
COPY src/ ./src/
COPY prompts/ ./prompts/
COPY tests/fixtures/sample_research.json tests/fixtures/

# Fix permissions
RUN chown -R jovyan:users /app

# Switch back to non-root user
USER jovyan

# Set environment variables that will be overridden by AWS Batch
ENV PYTHONUNBUFFERED=1 \
    AWS_DEFAULT_REGION=us-east-1

# Use the batch wrapper as entrypoint for AWS Batch
# This handles S3 input/output and status updates
ENTRYPOINT ["python", "batch_wrapper.py"]
# Default arguments can be overridden by Batch job parameters
CMD []