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
#include <Windows.h>
#include <strsafe.h>

using namespace web::http;
using namespace web::http::client;
using namespace pplx; 
using json = nlohmann::json;

struct HttpRequest {
    int statusCode;
    double requestDuration;
};

typedef struct RequestConfig {
    utility::string_t host;
    int port;
    bool useHttps;
    utility::string_t requestMethod;
    utility::string_t requestBody;
    utility::string_t uri;
    int clientCount;
    int delay;
    int processTime;
} REQUESTCONFIG, * PREQUESTCONFIG;

struct ThreadMetrics {
    int statusCode;
    double requestDuration;
};

typedef struct Params {
    PREQUESTCONFIG config;
} PARAMS, *PPARAMS;

void ErrorHandler(LPCTSTR lpszFunction);
HANDLE ghMutex;
std::vector<ThreadMetrics> main_stat_storage;



DWORD WINAPI TestEndpoint(LPVOID lpParam) {
    PPARAMS params = (PPARAMS)lpParam;
    RequestConfig* config = params->config;
    std::cout << "inside the thread" << std::endl;

    std::vector<ThreadMetrics> threadMetrics;
    /*utility::string_t url = config->useHttps ? U("https://") : U("http://") + config->host + U(":") + std::to_wstring(config->port) + U("/") + config->uri;
    std::cout << utility::conversions::to_utf8string(url);*/
    utility::string_t url = U("https://example.com");
    http_client client(url);
    for (int i = 0; i < config->processTime; i += config->delay) {
        auto startTime = std::chrono::high_resolution_clock::now();

        http_request request;
        request.set_method(config->requestMethod);

        if (config->requestMethod != U("GET") && config->requestMethod != U("DELETE")) {
            request.headers().set_content_type(U("application/json"));
            request.set_body(config->requestBody);
        }
        std::cout << "before the request" << std::endl;
        http_response response = client.request(request).get();
        std::cout << "after the request"<< response.status_code() << std::endl;
        auto endTime = std::chrono::high_resolution_clock::now();
        double duration = std::chrono::duration_cast<std::chrono::microseconds>(endTime - startTime).count() / 1000000.0;
        ThreadMetrics metric{ response.status_code(), duration };
        threadMetrics.push_back(metric);
        /*std::this_thread::sleep_for(std::chrono::seconds(config->delay));*/
        Sleep(config->delay);
    }

    DWORD dwWaitResult;
    dwWaitResult = WaitForSingleObject(
        ghMutex,    // handle to mutex
        INFINITE);  // no time-out interval

    switch (dwWaitResult)
    {
        // The thread got ownership of the mutex
    case WAIT_OBJECT_0:
        for (auto item : threadMetrics) {
            main_stat_storage.push_back(item);
        }
        if (!ReleaseMutex(ghMutex))
        {
            // Handle error.
        }
        break;

        // The thread got ownership of an abandoned mutex
        // The database is in an indeterminate state
    case WAIT_ABANDONED:
        return FALSE;
    }

    return 0;
}

int main() {
    // Чтение конфигурационного файла config.json
    std::vector<ThreadMetrics> s;
    ghMutex = CreateMutex(
        NULL,              
        FALSE,             
        NULL);

    if (ghMutex == NULL)
    {
        printf("CreateMutex error: %d\n", GetLastError());
        return 1;
    }
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


    PHANDLE hThreadArray = new HANDLE[requestConfig.clientCount]; // dynamically allocate memory
    PDWORD   dwThreadIdArray = new DWORD[requestConfig.clientCount];
    std::vector<std::vector<ThreadMetrics>> pMetricsArray;

    for (int i = 0; i < requestConfig.clientCount; i++)
    {
        PPARAMS params = new PARAMS{};
        params->config = &requestConfig;
       
;
        hThreadArray[i] = CreateThread(
            NULL,                   // default security attributes
            0,                      // use default stack size  
            TestEndpoint,           // thread function name
            params,          // argument to thread function 
            0,                      // use default creation flags 
            &dwThreadIdArray[i]);   // returns the thread identifier

        if (hThreadArray[i] == NULL)
        {
            ErrorHandler(TEXT("CreateThread"));
            ExitProcess(3);
        }
    }

    WaitForMultipleObjects(requestConfig.clientCount, hThreadArray, TRUE, INFINITE);


    for (int i = 0; i < requestConfig.clientCount; i++)
    {
        CloseHandle(hThreadArray[i]);
    }
// -------------
    // Создаем массив структур данных
    //std::vector<HttpRequest> httpRequests = {
    //    {200, 0.5},
    //    {404, 1.2},
    //    {200, 0.8},
    //    {500, 2.0},
    //    {404, 1.5}
    //    // Добавьте больше http-запросов по мере необходимости
    //};

    // Создаем словарь для подсчета статус-кодов
    std::unordered_map<int, int> statusCodeCount;

    // Переменные для вычисления среднего времени запроса
    double totalRequestDuration = 0;
    int totalRequests = main_stat_storage.size(); 

    for (const ThreadMetrics& request : main_stat_storage) {
        // Подсчет статус-кодов
        statusCodeCount[request.statusCode]++;

        // Вычисление общей продолжительности запросов
        totalRequestDuration += request.requestDuration;
        std::cout << request.requestDuration << std::endl;
    }

    // Вычисление среднего времени запроса
    double averageRequestDuration = totalRequestDuration / totalRequests;
    std::cout << averageRequestDuration << std::endl;

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

    std::cout << "Statistics was saved to file: " << filename << std::endl;

    return 0;
}


void ErrorHandler(LPCTSTR lpszFunction)
{
    // Retrieve the system error message for the last-error code.

    LPVOID lpMsgBuf;
    LPVOID lpDisplayBuf;
    DWORD dw = GetLastError();

    FormatMessage(
        FORMAT_MESSAGE_ALLOCATE_BUFFER |
        FORMAT_MESSAGE_FROM_SYSTEM |
        FORMAT_MESSAGE_IGNORE_INSERTS,
        NULL,
        dw,
        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        (LPTSTR)&lpMsgBuf,
        0, NULL);

    // Display the error message.

    lpDisplayBuf = (LPVOID)LocalAlloc(LMEM_ZEROINIT,
        (lstrlen((LPCTSTR)lpMsgBuf) + lstrlen((LPCTSTR)lpszFunction) + 40) * sizeof(TCHAR));
    StringCchPrintf((LPTSTR)lpDisplayBuf,
        LocalSize(lpDisplayBuf) / sizeof(TCHAR),
        TEXT("%s failed with error %d: %s"),
        lpszFunction, dw, lpMsgBuf);
    MessageBox(NULL, (LPCTSTR)lpDisplayBuf, TEXT("Error"), MB_OK);

    // Free error-handling buffer allocations.

    LocalFree(lpMsgBuf);
    LocalFree(lpDisplayBuf);
}