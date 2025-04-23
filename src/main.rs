use axum::{
    response::sse::{Event, Sse},
    routing::get,
    Router,
    http::HeaderName,
    response::IntoResponse,
    Json,
};
use futures::stream::{self, Stream};
use std::{convert::Infallible, time::Duration};
use tokio_stream::StreamExt;
use chrono::Utc;
use serde_json::{json, Value};

// 添加查询天使的函数
async fn query_angel() -> impl IntoResponse {
    let response = json!({
        "message": "这个世界存在天使"
    });
    
    Json(response)
}

async fn sse_handler() -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    let mut event_id = 0;
    
    // 创建事件流
    let stream = stream::repeat_with(move || {
        event_id += 1;
        let timestamp = Utc::now().timestamp_millis();
        let data = format!("{{\"timestamp\":{},\"message\":\"当前时间: {}\"}}",
            timestamp,
            Utc::now().format("%Y-%m-%d %H:%M:%S")
        );

        Ok(Event::default()
            .id(event_id.to_string())
            .event("message")
            .data(data))
    })
    .throttle(Duration::from_secs(1));

    // 配置SSE响应
    Sse::new(stream)
        .keep_alive(
            axum::response::sse::KeepAlive::new()
                .interval(Duration::from_secs(15))
                .text("")
        )
}

#[tokio::main]
async fn main() {
    // 创建路由
    let app = Router::new()
        .route("/events", get(sse_handler))
        .route("/query/angel", get(query_angel))  // 添加查询天使的路由
        .layer(
            tower_http::cors::CorsLayer::new()
                .allow_origin(tower_http::cors::Any)
                .allow_methods(tower_http::cors::Any)
                .allow_headers(tower_http::cors::Any)
                .expose_headers([HeaderName::from_static("content-type"), HeaderName::from_static("cache-control")])
                .max_age(Duration::from_secs(3600))
        );

    println!("服务器启动在 http://localhost:3000");
    println!("查询天使接口: http://localhost:3000/query/angel");

    // 启动服务器
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
