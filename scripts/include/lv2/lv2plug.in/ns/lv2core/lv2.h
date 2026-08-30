/*
 * LV2 Audio Plugin Specification Core Header
 * Compatibility wrapper for LV2 plugins
 */

#ifndef LV2_H_INCLUDED
#define LV2_H_INCLUDED

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define LV2_CORE_URI "http://lv2plug.in/ns/lv2core"
#define LV2_CORE_PREFIX LV2_CORE_URI "#"

#define LV2_CORE__AudioPort           LV2_CORE_PREFIX "AudioPort"
#define LV2_CORE__ControlPort         LV2_CORE_PREFIX "ControlPort"
#define LV2_CORE__CVPort              LV2_CORE_PREFIX "CVPort"
#define LV2_CORE__InputPort           LV2_CORE_PREFIX "InputPort"
#define LV2_CORE__OutputPort          LV2_CORE_PREFIX "OutputPort"
#define LV2_CORE__Point               LV2_CORE_PREFIX "Point"
#define LV2_CORE__Port                LV2_CORE_PREFIX "Port"
#define LV2_CORE__PortProperty        LV2_CORE_PREFIX "PortProperty"
#define LV2_CORE__Resource            LV2_CORE_PREFIX "Resource"
#define LV2_CORE__ScalePoint          LV2_CORE_PREFIX "ScalePoint"
#define LV2_CORE__Specification       LV2_CORE_PREFIX "Specification"
#define LV2_CORE__Plugin              LV2_CORE_PREFIX "Plugin"

#define LV2_CORE__appliesTo           LV2_CORE_PREFIX "appliesTo"
#define LV2_CORE__binary              LV2_CORE_PREFIX "binary"
#define LV2_CORE__default             LV2_CORE_PREFIX "default"
#define LV2_CORE__designation         LV2_CORE_PREFIX "designation"
#define LV2_CORE__documentation       LV2_CORE_PREFIX "documentation"
#define LV2_CORE__enumeration         LV2_CORE_PREFIX "enumeration"
#define LV2_CORE__extensionData       LV2_CORE_PREFIX "extensionData"
#define LV2_CORE__freePath            LV2_CORE_PREFIX "freePath"
#define LV2_CORE__hardRTCapable        LV2_CORE_PREFIX "hardRTCapable"
#define LV2_CORE__inPlaceBroken       LV2_CORE_PREFIX "inPlaceBroken"
#define LV2_CORE__index               LV2_CORE_PREFIX "index"
#define LV2_CORE__integer             LV2_CORE_PREFIX "integer"
#define LV2_CORE__isLive              LV2_CORE_PREFIX "isLive"
#define LV2_CORE__maximum             LV2_CORE_PREFIX "maximum"
#define LV2_CORE__microVersion        LV2_CORE_PREFIX "microVersion"
#define LV2_CORE__minimum             LV2_CORE_PREFIX "minimum"
#define LV2_CORE__minorVersion        LV2_CORE_PREFIX "minorVersion"
#define LV2_CORE__name                LV2_CORE_PREFIX "name"
#define LV2_CORE__optionalFeature     LV2_CORE_PREFIX "optionalFeature"
#define LV2_CORE__port                LV2_CORE_PREFIX "port"
#define LV2_CORE__portProperty        LV2_CORE_PREFIX "portProperty"
#define LV2_CORE__reportsLatency      LV2_CORE_PREFIX "reportsLatency"
#define LV2_CORE__requiredFeature     LV2_CORE_PREFIX "requiredFeature"
#define LV2_CORE__sampleRate          LV2_CORE_PREFIX "sampleRate"
#define LV2_CORE__scalePoint          LV2_CORE_PREFIX "scalePoint"
#define LV2_CORE__symbol              LV2_CORE_PREFIX "symbol"
#define LV2_CORE__toggled             LV2_CORE_PREFIX "toggled"

#if defined(_WIN32) || defined(__CYGWIN__)
  #define LV2_SYMBOL_EXPORT __declspec(dllexport)
#else
  #define LV2_SYMBOL_EXPORT __attribute__((visibility("default")))
#endif

typedef void* LV2_Handle;

typedef struct _LV2_Feature {
    const char* URI;
    void* data;
} LV2_Feature;

typedef struct _LV2_Descriptor {
    const char* URI;
    LV2_Handle (*instantiate)(const struct _LV2_Descriptor* descriptor,
                              double sample_rate,
                              const char* bundle_path,
                              const LV2_Feature* const* features);
    void (*connect_port)(LV2_Handle instance,
                         uint32_t port,
                         void* data_location);
    void (*activate)(LV2_Handle instance);
    void (*run)(LV2_Handle instance, uint32_t sample_count);
    void (*deactivate)(LV2_Handle instance);
    void (*cleanup)(LV2_Handle instance);
    const void* (*extension_data)(const char* uri);
} LV2_Descriptor;

#ifdef __cplusplus
}
#endif

#endif /* LV2_H_INCLUDED */
