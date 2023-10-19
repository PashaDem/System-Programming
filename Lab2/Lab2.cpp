#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <chrono>
#include <thread>
#include <cstdlib>
#include <ctime>
#include <windows.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;


LPCWSTR ConvertToLPCWSTR(const char* charString) {
    int size = MultiByteToWideChar(CP_UTF8, 0, charString, -1, NULL, 0);
    wchar_t* wideString = new wchar_t[size];
    MultiByteToWideChar(CP_UTF8, 0, charString, -1, wideString, size);

    return wideString;
}

// Function to create a new process
void createNewProcess(const std::string& pathToExe) {
    STARTUPINFO si;
    PROCESS_INFORMATION pi;

    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));
    LPCWSTR pathToExecutable = ConvertToLPCWSTR(pathToExe.c_str());

    if (CreateProcess(pathToExecutable, NULL, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        std::cout << "Created a new process for: " << pathToExe << std::endl;
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }
    else {
        std::cerr << "Failed to create a new process for: " << pathToExe << std::endl;
    }
}




int main() {
    std::ifstream configFile("config.json");
    if (!configFile) {
        std::cerr << "Failed to open config.json" << std::endl;
        return 1;
    }

    json config;
    configFile >> config;

    std::vector<json> processList = config;

    // Initialize the 'last_created' field for each item in the process list
    for (auto& item : processList) {
        item["last_created"] = 0;
    }

    while (true) {
        try {
            auto currentTime = std::chrono::system_clock::now();
            auto currentTimestamp = std::chrono::duration_cast<std::chrono::minutes>(currentTime.time_since_epoch()).count();

            // Create new processes and update 'last_created' field
            for (auto& item : processList) {
                auto lastCreated = item["last_created"].get<int>();
                auto periodInMinutes = item["periodInMinutes"].get<int>();

                if (currentTimestamp - lastCreated >= periodInMinutes) {
                    createNewProcess(item["pathToExe"].get<std::string>());
                    item["last_created"] = currentTimestamp;
                }
            }

            // Sleep for a while before checking again
            std::this_thread::sleep_for(std::chrono::minutes(1));

            // Check and clear ended processes (not implemented here)
        }
        catch (const std::exception & e) {
            std::cout << e.what() << std::endl;
        }
        
    }

    return 0;
}