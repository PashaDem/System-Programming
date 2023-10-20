#include <iostream>
#include <string>
#include <windows.h>
using namespace std;

int main()
{
    int sum = 0;
    string appName = "test_app1";

    for (int counter = 0; counter < 100; ++counter)
    {
        sum += counter;
        cout << appName << ":: Iteration number ::" << counter << endl;
        Sleep(1000);
        if (counter == 10) {
            throw std::invalid_argument("each time counter == 10 I throw an exception");
        }
    }
    cout << sum << endl;
}
