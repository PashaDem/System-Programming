#include <iostream>
#include <fstream>
#include <cpprest/http_client.h>
#include <cpprest/http_msg.h>
#include <cpprest/filestream.h>
#include <cpprest/streams.h>
#include <chrono>
#include <vector>
#include <thread>
#include <ppl.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <unordered_map>
#include <nlohmann/json.hpp>
#include <chrono>

using namespace web::http;
using namespace web::http::client;
using namespace pplx; 
using json = nlohmann::json;

struct HttpRequest {
    int statusCode;
    double requestDuration;
};

struct RequestConfig {
    utility::string_t host;
    int port;
    bool useHttps;
    utility::string_t requestMethod;
    utility::string_t requestBody;
    utility::string_t uri;
    int clientCount;
    int delay;
    int processTime;
};

struct ThreadMetrics {
    int statusCode;
    double requestDuration;
};

std::vector<ThreadMetrics> statistics;



void PerformStressTest(const RequestConfig& config, std::vector<ThreadMetrics>& threadMetrics, int threadId) {
    http_client client(config.useHttps ? U("https://") : U("http://") + config.host + U(":") + std::to_wstring(config.port) + U("/") + config.uri);

    for (int i = 0; i < config.processTime; i += config.delay) {
        auto startTime = std::chrono::high_resolution_clock::now();

        http_request request;
        request.set_method(config.requestMethod);

        if (config.requestMethod != U("GET") && config.requestMethod != U("DELETE")) {
            request.headers().set_content_type(U("application/json"));
            request.set_body(config.requestBody);
        }

        client.request(request).then([startTime, &threadMetrics, i, threadId](http_response response) {
            auto endTime = std::chrono::high_resolution_clock::now();
            double duration = std::chrono::duration_cast<std::chrono::microseconds>(endTime - startTime).count() / 1000000.0;

            ThreadMetrics metrics;
            metrics.statusCode = response.status_code();
            metrics.requestDuration = duration;

            /*threadMetrics[i / config.delay] = metrics;*/

            }).wait();

            std::this_thread::sleep_for(std::chrono::seconds(config.delay));
    }
}

int main() {
    // Чтение конфигурационного файла config.json
    utility::ifstream_t configStream(U("config.json"));
    web::json::value config;
    configStream >> config;
    RequestConfig requestConfig;

    requestConfig.host = config[U("host")].as_string();
    requestConfig.port = config[U("port")].as_integer();
    requestConfig.useHttps = config[U("use_https")].as_bool();
    requestConfig.requestMethod = config[U("request_method")].as_string();
    requestConfig.requestBody = config[U("request_body")].as_string();
    requestConfig.uri = config[U("uri")].as_string();
    requestConfig.clientCount = config[U("client_count")].as_integer();
    requestConfig.delay = config[U("delay")].as_integer();
    requestConfig.processTime = config[U("process_time")].as_integer();

    
// -------------
    // Создаем массив структур данных
    std::vector<HttpRequest> httpRequests = {
        {200, 0.5},
        {404, 1.2},
        {200, 0.8},
        {500, 2.0},
        {404, 1.5}
        // Добавьте больше http-запросов по мере необходимости
    };

    // Создаем словарь для подсчета статус-кодов
    std::unordered_map<int, int> statusCodeCount;

    // Переменные для вычисления среднего времени запроса
    double totalRequestDuration = 0;
    int totalRequests = httpRequests.size(); 

    for (const HttpRequest& request : httpRequests) {
        // Подсчет статус-кодов
        statusCodeCount[request.statusCode]++;

        // Вычисление общей продолжительности запросов
        totalRequestDuration += request.requestDuration;
    }

    // Вычисление среднего времени запроса
    double averageRequestDuration = totalRequestDuration / totalRequests;

    // Создаем JSON-объект для хранения статистики
    json statistics;
    statistics["averageRequestDuration"] = averageRequestDuration;
    statistics["codes"] = json::object();

    // Заполнение поля "codes" в JSON-объекте
    for (const auto& entry : statusCodeCount) {
        statistics["codes"][std::to_string(entry.first)] = entry.second;
    }

    // Получение текущей даты и времени
    auto now = std::chrono::system_clock::now();
    auto time = std::chrono::system_clock::to_time_t(now);

    // Форматирование даты и времени
    std::tm tm = *std::localtime(&time);
    char datetime[20];
    std::strftime(datetime, sizeof(datetime), "%Y-%m-%d-%H-%M-%S", &tm);

    // Создание имени файла с текущей датой и временем
    std::string filename = "statistics-" + std::string(datetime) + ".json";

    // Сохранение JSON-объекта в файл
    std::ofstream outputFile(filename);
    outputFile << statistics.dump(4); // Укажите желаемое количество отступов

    std::cout << "Статистика сохранена в файл: " << filename << std::endl;

    return 0;
}