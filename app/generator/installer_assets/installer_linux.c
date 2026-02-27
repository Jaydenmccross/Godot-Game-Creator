/*
 * Godot Game Creator — Linux Installer
 *
 * A lightweight terminal-based installer that:
 *   1. Downloads portable Godot Engine
 *   2. Creates a launcher script
 *   3. Creates a .desktop file
 *   4. Launches the game
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include <limits.h>

#define GODOT_URL "https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_linux.x86_64.zip"
#define GODOT_BIN "Godot_v4.4.1-stable_linux.x86_64"
#define ENGINE_DIR "engine"

static char game_name[256] = "Godot Game";
static char install_dir[PATH_MAX];

static void read_game_name(void);
static int download_godot(void);
static int create_launcher(void);
static int create_desktop_entry(void);

int main(void)
{
    if (!getcwd(install_dir, sizeof(install_dir))) {
        perror("getcwd");
        return 1;
    }

    read_game_name();

    printf("\n");
    printf("╔══════════════════════════════════════════╗\n");
    printf("║     %s Installer            ║\n", game_name);
    printf("║     Powered by Godot Game Creator        ║\n");
    printf("╚══════════════════════════════════════════╝\n");
    printf("\n");

    /* Check if engine already exists */
    char exe_path[PATH_MAX];
    snprintf(exe_path, sizeof(exe_path), "%s/%s/%s", install_dir, ENGINE_DIR, GODOT_BIN);

    struct stat st;
    if (stat(exe_path, &st) == 0) {
        printf("[✓] Godot Engine already installed.\n");
    } else {
        printf("[1/3] Downloading Godot Engine...\n");
        if (!download_godot()) {
            fprintf(stderr, "ERROR: Failed to download Godot Engine.\n");
            return 1;
        }
        printf("[✓] Godot Engine downloaded.\n");
    }

    printf("[2/3] Creating launcher...\n");
    create_launcher();
    printf("[✓] Launcher created.\n");

    printf("[3/3] Creating desktop entry...\n");
    create_desktop_entry();
    printf("[✓] Desktop entry created.\n");

    printf("\n");
    printf("═══════════════════════════════════════════\n");
    printf("  Installation complete!\n");
    printf("  Run ./Play.sh or use the desktop shortcut.\n");
    printf("═══════════════════════════════════════════\n");
    printf("\n");

    /* Ask to launch */
    printf("Launch game now? [Y/n] ");
    fflush(stdout);
    int c = getchar();
    if (c == 'n' || c == 'N') return 0;

    char cmd[PATH_MAX * 2];
    snprintf(cmd, sizeof(cmd),
        "\"%s/%s/%s\" --path \"%s\" --windowed &",
        install_dir, ENGINE_DIR, GODOT_BIN, install_dir);
    system(cmd);

    return 0;
}

static void read_game_name(void)
{
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
                    strncpy(game_name, start, sizeof(game_name) - 1);
                }
            }
            break;
        }
    }
    fclose(fp);
}

static int download_godot(void)
{
    mkdir(ENGINE_DIR, 0755);

    char cmd[1024];
    snprintf(cmd, sizeof(cmd),
        "wget -q --show-progress -O '%s/godot.zip' '%s' 2>&1"
        " || curl -L -o '%s/godot.zip' '%s'",
        ENGINE_DIR, GODOT_URL, ENGINE_DIR, GODOT_URL);

    if (system(cmd) != 0) return 0;

    snprintf(cmd, sizeof(cmd),
        "unzip -o '%s/godot.zip' -d '%s' && rm '%s/godot.zip'",
        ENGINE_DIR, ENGINE_DIR, ENGINE_DIR);

    if (system(cmd) != 0) return 0;

    char exe[PATH_MAX];
    snprintf(exe, sizeof(exe), "%s/%s/%s", install_dir, ENGINE_DIR, GODOT_BIN);
    chmod(exe, 0755);

    return 1;
}

static int create_launcher(void)
{
    FILE *fp = fopen("Play.sh", "w");
    if (!fp) return 0;
    fprintf(fp, "#!/bin/bash\n");
    fprintf(fp, "cd \"$(dirname \"$0\")\"\n");
    fprintf(fp, "if [ -f \"%s/%s\" ]; then\n", ENGINE_DIR, GODOT_BIN);
    fprintf(fp, "    ./%s/%s --path . --windowed \"$@\"\n", ENGINE_DIR, GODOT_BIN);
    fprintf(fp, "else\n");
    fprintf(fp, "    echo \"Godot not found. Run ./setup first.\"\n");
    fprintf(fp, "fi\n");
    fclose(fp);
    chmod("Play.sh", 0755);
    return 1;
}

static int create_desktop_entry(void)
{
    char *home = getenv("HOME");
    if (!home) return 0;

    char dir[PATH_MAX];
    snprintf(dir, sizeof(dir), "%s/.local/share/applications", home);
    mkdir(dir, 0755);

    char path[PATH_MAX];
    snprintf(path, sizeof(path), "%s/%s.desktop", dir, game_name);

    FILE *fp = fopen(path, "w");
    if (!fp) return 0;

    fprintf(fp, "[Desktop Entry]\n");
    fprintf(fp, "Type=Application\n");
    fprintf(fp, "Name=%s\n", game_name);
    fprintf(fp, "Exec=%s/%s/%s --path %s --windowed\n",
        install_dir, ENGINE_DIR, GODOT_BIN, install_dir);
    fprintf(fp, "Path=%s\n", install_dir);
    fprintf(fp, "Terminal=false\n");
    fprintf(fp, "Categories=Game;\n");
    fclose(fp);

    return 1;
}
