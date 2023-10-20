#include <iostream>
#include <Windows.h>
#include <string>


using namespace std;

    
    void bubbleSort(int arr[], int n)
    {
        string appName = "test_app_2";
        int i, j;
        for (i = 0; i < n - 1; i++) {
            
            for (j = 0; j < n - i - 1; j++)
            {
                Sleep(1000);
                cout << "process :: " << appName << " :: iterated again " << "i: " << i << " j: " << j << endl;
                if (arr[j] > arr[j + 1])
                    swap(arr[j], arr[j + 1]);
            }
        }   
    }

    void printArray(int arr[], int size)
    {
        int i;
        for (i = 0; i < size; i++)
            cout << arr[i] << " ";
        cout << endl;
    }

    int main()
    {
        string appName = "test_app_2";
        int arr[] = { 5, 1, 4, 2, 8 };
        cout << "process :: " + appName << "has started" << endl;
        for (int i = 0; i < 5; ++i) {
            cout << arr[i] << " ";
        }
        cout << endl;
        int N = sizeof(arr) / sizeof(arr[0]);
        bubbleSort(arr, N);
        cout << "process" + appName + " Sorted array: \n";
        printArray(arr, N);
        return 0;
    }