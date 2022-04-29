FROM public.ecr.aws/lambda/python:3.9

ADD src ${LAMBDA_TASK_ROOT}/src
COPY main.py ${LAMBDA_TASK_ROOT}

COPY requirements.txt  .

RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

CMD [ "main.handler" ]
