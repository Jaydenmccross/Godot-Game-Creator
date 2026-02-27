/*
 * Godot Game Creator — Windows Installer
 *
 * A lightweight native Windows installer that:
 *   1. Shows a setup wizard UI
 *   2. Downloads portable Godot Engine
 *   3. Creates a Play shortcut on the Desktop
 *   4. Launches the game
 *
 * Compiled with: x86_64-w64-mingw32-gcc -o Setup.exe installer.c
 *                -lwininet -lole32 -luuid -mwindows
 */

#include <windows.h>
#include <wininet.h>
#include <shlobj.h>
#include <stdio.h>
#include <string.h>

#define GODOT_URL "https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_win64.exe.zip"
#define GODOT_EXE "Godot_v4.4.1-stable_win64.exe"
#define ENGINE_DIR "engine"
#define BUF_SIZE 8192

static char g_game_name[256] = "Godot Game";
static char g_install_dir[MAX_PATH];
static HWND g_hwnd = NULL;
static HWND g_progress = NULL;
static HWND g_status = NULL;

/* Forward declarations */
LRESULT CALLBACK WndProc(HWND, UINT, WPARAM, LPARAM);
static int DoInstall(void);
static int DownloadFile(const char *url, const char *dest);
static int UnzipFile(const char *zip, const char *dest_dir);
static void CreateDesktopShortcut(void);
static void ReadGameName(void);
static void SetStatus(const char *msg);

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrev,
                   LPSTR lpCmd, int nShow)
{
    (void)hPrev; (void)lpCmd;

    ReadGameName();
    GetCurrentDirectoryA(MAX_PATH, g_install_dir);

    WNDCLASSA wc = {0};
    wc.lpfnWndProc   = WndProc;
    wc.hInstance      = hInstance;
    wc.hbrBackground  = (HBRUSH)(COLOR_WINDOW + 1);
    wc.lpszClassName  = "GGCInstaller";
    wc.hCursor        = LoadCursor(NULL, IDC_ARROW);
    RegisterClassA(&wc);

    char title[300];
    snprintf(title, sizeof(title), "Install %s", g_game_name);

    g_hwnd = CreateWindowA("GGCInstaller", title,
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 480, 320,
        NULL, NULL, hInstance, NULL);

    ShowWindow(g_hwnd, nShow);
    UpdateWindow(g_hwnd);

    MSG msg;
    while (GetMessageA(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageA(&msg);
    }
    return (int)msg.wParam;
}

LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    switch (msg) {
    case WM_CREATE: {
        char welcome[512];
        snprintf(welcome, sizeof(welcome),
            "Welcome to the %s Installer!\n\n"
            "This will set up the game engine and create\n"
            "a desktop shortcut so you can play instantly.\n\n"
            "Click Install to begin.", g_game_name);

        CreateWindowA("STATIC", welcome,
            WS_VISIBLE | WS_CHILD | SS_LEFT,
            20, 15, 430, 120, hwnd, NULL, NULL, NULL);

        g_status = CreateWindowA("STATIC", "Ready to install",
            WS_VISIBLE | WS_CHILD | SS_LEFT,
            20, 150, 430, 20, hwnd, (HMENU)201, NULL, NULL);

        g_progress = CreateWindowA("msctls_progress32", NULL,
            WS_VISIBLE | WS_CHILD | PBS_SMOOTH,
            20, 180, 430, 22, hwnd, (HMENU)202, NULL, NULL);
        SendMessage(g_progress, PBM_SETRANGE, 0, MAKELPARAM(0, 100));

        CreateWindowA("BUTTON", "Install",
            WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,
            260, 230, 90, 32, hwnd, (HMENU)101, NULL, NULL);

        CreateWindowA("BUTTON", "Cancel",
            WS_VISIBLE | WS_CHILD,
            360, 230, 90, 32, hwnd, (HMENU)102, NULL, NULL);
        break;
    }
    case WM_COMMAND:
        if (LOWORD(wp) == 101) {
            EnableWindow(GetDlgItem(hwnd, 101), FALSE);
            if (DoInstall()) {
                char done[256];
                snprintf(done, sizeof(done),
                    "%s has been installed!\nA shortcut was placed on your Desktop.",
                    g_game_name);
                MessageBoxA(hwnd, done, "Installation Complete",
                    MB_OK | MB_ICONINFORMATION);

                /* Launch the game */
                char cmd[MAX_PATH * 2];
                snprintf(cmd, sizeof(cmd),
                    "\"%s\\%s\\%s\" --path \"%s\" --windowed",
                    g_install_dir, ENGINE_DIR, GODOT_EXE,
                    g_install_dir);
                STARTUPINFOA si = { sizeof(si) };
                PROCESS_INFORMATION pi;
                CreateProcessA(NULL, cmd, NULL, NULL, FALSE,
                    0, NULL, NULL, &si, &pi);
                CloseHandle(pi.hThread);
                CloseHandle(pi.hProcess);
            }
            PostQuitMessage(0);
        }
        else if (LOWORD(wp) == 102) {
            PostQuitMessage(0);
        }
        break;
    case WM_DESTROY:
        PostQuitMessage(0);
        break;
    default:
        return DefWindowProcA(hwnd, msg, wp, lp);
    }
    return 0;
}

static void SetStatus(const char *msg)
{
    SetWindowTextA(g_status, msg);
    UpdateWindow(g_status);
}

static void SetProgress(int pct)
{
    SendMessage(g_progress, PBM_SETPOS, pct, 0);
    UpdateWindow(g_progress);
}

static int DoInstall(void)
{
    char engine_path[MAX_PATH];
    snprintf(engine_path, sizeof(engine_path), "%s\\%s", g_install_dir, ENGINE_DIR);

    /* Check if Godot already exists */
    char exe_path[MAX_PATH];
    snprintf(exe_path, sizeof(exe_path), "%s\\%s", engine_path, GODOT_EXE);

    WIN32_FIND_DATAA fd;
    HANDLE hf = FindFirstFileA(exe_path, &fd);
    if (hf != INVALID_HANDLE_VALUE) {
        FindClose(hf);
        SetStatus("Godot Engine already installed!");
        SetProgress(80);
    } else {
        CreateDirectoryA(engine_path, NULL);

        SetStatus("Downloading Godot Engine...");
        SetProgress(10);

        char zip_path[MAX_PATH];
        snprintf(zip_path, sizeof(zip_path), "%s\\godot.zip", engine_path);

        if (!DownloadFile(GODOT_URL, zip_path)) {
            MessageBoxA(g_hwnd, "Failed to download Godot Engine.\n"
                "Please check your internet connection.",
                "Download Error", MB_OK | MB_ICONERROR);
            return 0;
        }
        SetProgress(60);

        SetStatus("Extracting Godot Engine...");
        if (!UnzipFile(zip_path, engine_path)) {
            MessageBoxA(g_hwnd, "Failed to extract Godot Engine.",
                "Extract Error", MB_OK | MB_ICONERROR);
            return 0;
        }
        DeleteFileA(zip_path);
        SetProgress(80);
    }

    SetStatus("Creating desktop shortcut...");
    CreateDesktopShortcut();
    SetProgress(100);
    SetStatus("Installation complete!");
    return 1;
}

static int DownloadFile(const char *url, const char *dest)
{
    HINTERNET hNet = InternetOpenA("GGC-Installer/1.0", INTERNET_OPEN_TYPE_PRECONFIG,
        NULL, NULL, 0);
    if (!hNet) return 0;

    HINTERNET hUrl = InternetOpenUrlA(hNet, url, NULL, 0,
        INTERNET_FLAG_RELOAD | INTERNET_FLAG_NO_CACHE_WRITE, 0);
    if (!hUrl) { InternetCloseHandle(hNet); return 0; }

    FILE *fp = fopen(dest, "wb");
    if (!fp) { InternetCloseHandle(hUrl); InternetCloseHandle(hNet); return 0; }

    char buf[BUF_SIZE];
    DWORD read;
    while (InternetReadFile(hUrl, buf, BUF_SIZE, &read) && read > 0) {
        fwrite(buf, 1, read, fp);
    }

    fclose(fp);
    InternetCloseHandle(hUrl);
    InternetCloseHandle(hNet);
    return 1;
}

static int UnzipFile(const char *zip, const char *dest_dir)
{
    /* Use PowerShell for extraction — simplest reliable approach */
    char cmd[MAX_PATH * 3];
    snprintf(cmd, sizeof(cmd),
        "powershell -NoProfile -Command \"Expand-Archive -Path '%s' -DestinationPath '%s' -Force\"",
        zip, dest_dir);

    STARTUPINFOA si = { sizeof(si) };
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;
    PROCESS_INFORMATION pi;

    if (!CreateProcessA(NULL, cmd, NULL, NULL, FALSE,
            CREATE_NO_WINDOW, NULL, NULL, &si, &pi))
        return 0;

    WaitForSingleObject(pi.hProcess, 120000);
    DWORD exitCode;
    GetExitCodeProcess(pi.hProcess, &exitCode);
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return exitCode == 0;
}

static void CreateDesktopShortcut(void)
{
    /* Create a .bat launcher on the Desktop */
    char desktop[MAX_PATH];
    if (FAILED(SHGetFolderPathA(NULL, CSIDL_DESKTOPDIRECTORY, NULL, 0, desktop)))
        return;

    char shortcut[MAX_PATH];
    snprintf(shortcut, sizeof(shortcut), "%s\\%s.bat", desktop, g_game_name);

    FILE *fp = fopen(shortcut, "w");
    if (!fp) return;
    fprintf(fp, "@echo off\r\n");
    fprintf(fp, "cd /d \"%s\"\r\n", g_install_dir);
    fprintf(fp, "start \"\" \"%s\\%s\\%s\" --path \"%s\" --windowed\r\n",
        g_install_dir, ENGINE_DIR, GODOT_EXE, g_install_dir);
    fclose(fp);
}

static void ReadGameName(void)
{
    /* Read game name from project.godot */
    FILE *fp = fopen("project.godot", "r");
    if (!fp) return;

    char line[512];
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "config/name=", 12) == 0) {
            char *start = strchr(line, '"');
            if (start) {
                start++;
                char *end = strchr(start, '"');
                if (end) {
                    *end = '\0';
                    strncpy(g_game_name, start, sizeof(g_game_name) - 1);
                }
            }
            break;
        }
    }
    fclose(fp);
}
