# wordscheck — 敏感词检测服务 Dockerfile
# 项目地址: https://github.com/tossp/wordscheck
# 本文件仅供本地构建使用，实际使用时从官方源拉取

FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o wordscheck .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /app
COPY --from=builder /app/wordscheck .
EXPOSE 8080
CMD ["./wordscheck"]
