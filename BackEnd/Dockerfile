FROM selenium/node-chrome
USER root

RUN apt-get update \
    && apt-get -y install ttf-wqy-microhei ttf-wqy-zenhei \
    && apt-get clean
RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev
RUN apt-get install -y python3 && apt-get install -y python3-pip
COPY requirements.txt ./

RUN pip3 install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
COPY ./app /app/
COPY ./run.py /
CMD ["gunicorn", "-w", "9", "-b", ":8000", "run:app"]