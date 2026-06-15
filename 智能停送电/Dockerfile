FROM python:3.11-slim

# 设置环境变量
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 安装系统依赖和中文语言包
RUN apt-get update && apt-get install -y \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && localedef -i zh_CN -c -f UTF-8 -A /usr/share/locale/locale.alias zh_CN.UTF-8

# 设置中文环境
ENV LANG zh_CN.UTF-8
ENV LANGUAGE zh_CN:zh
ENV LC_ALL zh_CN.UTF-8

# 先复制requirements.txt
COPY shared/requirements.txt ./

# 安装依赖
RUN pip install -r requirements.txt

# 复制应用文件
COPY server_new.py ./
COPY app ./app
COPY web_pages ./web_pages
COPY tools ./tools
COPY shared/common ./common

EXPOSE 5050

CMD ["python", "server_new.py"]
