# ---- Build stage ----
FROM public.ecr.aws/lambda/python:3.11 as build

# Install system dependencies for scientific packages
RUN yum -y install gcc gcc-c++ blas-devel lapack-devel atlas-devel

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir --prefix=/root/python -r requirements.txt

# ---- Runtime stage ----
FROM public.ecr.aws/lambda/python:3.11

# Copy installed packages from build stage
COPY --from=build /root/python /opt/python

# Copy Lambda handler and all necessary modules
COPY lambda_cluster_jtbd.py .
COPY cluster_jtbd.py .

# Set environment for Python to find packages
ENV PYTHONPATH=/opt/python/lib/python3.11/site-packages:/opt/python

# Lambda handler
CMD ["lambda_cluster_jtbd.lambda_handler"]