#define _GNU_SOURCE

#include <dlfcn.h>
#include <string.h>

#define PILIPLUS_APP_ID "com.example.piliplus"
#define PILIPLUS_APP_NAME "PiliPlus"

typedef void AppIndicator;
typedef AppIndicator *(*app_indicator_new_fn)(const char *id,
                                              const char *icon_name,
                                              int category);
typedef void (*app_indicator_set_icon_full_fn)(AppIndicator *self,
                                               const char *icon_name,
                                               const char *icon_desc);
typedef void (*app_indicator_set_label_fn)(AppIndicator *self,
                                           const char *label,
                                           const char *guide);

static int looks_like_piliplus_asset_icon(const char *icon_name) {
  if (icon_name == NULL || icon_name[0] == '\0') {
    return 1;
  }

  return strstr(icon_name, "assets/images/logo/") != NULL ||
         strstr(icon_name, "PiliPlus/data/flutter_assets/") != NULL;
}

static const char *normalise_icon_name(const char *icon_name) {
  if (looks_like_piliplus_asset_icon(icon_name)) {
    return PILIPLUS_APP_ID;
  }

  return icon_name;
}

static const char *normalise_label(const char *label) {
  if (label == NULL || label[0] == '\0' ||
      looks_like_piliplus_asset_icon(label)) {
    return PILIPLUS_APP_NAME;
  }

  return label;
}

AppIndicator *app_indicator_new(const char *id, const char *icon_name,
                                int category) {
  app_indicator_new_fn real_app_indicator_new =
      (app_indicator_new_fn)dlsym(RTLD_NEXT, "app_indicator_new");

  return real_app_indicator_new(PILIPLUS_APP_ID, normalise_icon_name(icon_name),
                                category);
}

void app_indicator_set_icon_full(AppIndicator *self, const char *icon_name,
                                 const char *icon_desc) {
  app_indicator_set_icon_full_fn real_app_indicator_set_icon_full =
      (app_indicator_set_icon_full_fn)dlsym(RTLD_NEXT,
                                            "app_indicator_set_icon_full");

  real_app_indicator_set_icon_full(self, normalise_icon_name(icon_name),
                                   icon_desc);
}

void app_indicator_set_label(AppIndicator *self, const char *label,
                             const char *guide) {
  app_indicator_set_label_fn real_app_indicator_set_label =
      (app_indicator_set_label_fn)dlsym(RTLD_NEXT, "app_indicator_set_label");

  real_app_indicator_set_label(self, normalise_label(label), guide);
}
