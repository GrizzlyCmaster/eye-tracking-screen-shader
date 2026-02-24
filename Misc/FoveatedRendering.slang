// Foveated Rendering / Gaze-Contingent Display shader
// Uses variable sampling resolution based on eye gaze position
// High detail at center (fovea), lower detail in periphery
// NO distortion - safe for motion sickness

#version 450

#pragma parameter FoveaRadius "Fovea Radius (high detail)" 0.15 0.05 0.4 0.01
#pragma parameter TransitionRadius "Transition Radius" 0.35 0.15 0.6 0.01
#pragma parameter PeripheralBlur "Peripheral Blur Amount" 2.0 0.0 5.0 0.1
#pragma parameter CenterX "Center X (Eye Track)" 0.5 0.0 1.0 0.01
#pragma parameter CenterY "Center Y (Eye Track)" 0.5 0.0 1.0 0.01
#pragma parameter Sharpness "Center Sharpness Boost" 1.2 1.0 2.0 0.1

layout(push_constant) uniform Push
{
    vec4 SourceSize;
    vec4 OriginalSize;
    vec4 OutputSize;
    uint FrameCount;

    float FoveaRadius;
    float TransitionRadius;
    float PeripheralBlur;
    float CenterX;
    float CenterY;
    float Sharpness;
} params;

layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
} global;

#pragma stage vertex

layout(location = 0) in vec4 Position;
layout(location = 1) in vec2 TexCoord;
layout(location = 0) out vec2 vTexCoord;

void main()
{
    gl_Position = global.MVP * Position;
    vTexCoord = TexCoord;
}

#pragma stage fragment

layout(location = 0) in vec2 vTexCoord;
layout(location = 0) out vec4 FragColor;
layout(set = 0, binding = 2) uniform sampler2D Source;

// Fast Gaussian blur approximation
vec3 sampleBlur(vec2 uv, float blur_amount)
{
    vec2 pixel_size = 1.0 / params.SourceSize.xy;
    vec3 color = vec3(0.0);
    
    if(blur_amount < 0.1)
    {
        // No blur needed - direct sample
        return texture(Source, uv).rgb;
    }
    
    // 9-tap blur (box filter approximation)
    float radius = blur_amount * pixel_size.x;
    
    color += texture(Source, uv + vec2(-radius, -radius)).rgb;
    color += texture(Source, uv + vec2(0.0, -radius)).rgb;
    color += texture(Source, uv + vec2(radius, -radius)).rgb;
    
    color += texture(Source, uv + vec2(-radius, 0.0)).rgb;
    color += texture(Source, uv).rgb * 2.0; // Center weighted
    color += texture(Source, uv + vec2(radius, 0.0)).rgb;
    
    color += texture(Source, uv + vec2(-radius, radius)).rgb;
    color += texture(Source, uv + vec2(0.0, radius)).rgb;
    color += texture(Source, uv + vec2(radius, radius)).rgb;
    
    return color / 10.0;
}

// Apply unsharp mask for center sharpening
vec3 sharpen(vec3 center, vec2 uv)
{
    vec2 pixel_size = 1.0 / params.SourceSize.xy;
    
    vec3 blur = vec3(0.0);
    blur += texture(Source, uv + vec2(-pixel_size.x, 0.0)).rgb;
    blur += texture(Source, uv + vec2(pixel_size.x, 0.0)).rgb;
    blur += texture(Source, uv + vec2(0.0, -pixel_size.y)).rgb;
    blur += texture(Source, uv + vec2(0.0, pixel_size.y)).rgb;
    blur /= 4.0;
    
    return center + (center - blur) * (params.Sharpness - 1.0);
}

void main()
{
    vec2 gaze_center = vec2(params.CenterX, params.CenterY);
    
    // Calculate distance from gaze point (corrected for aspect ratio)
    vec2 offset = vTexCoord - gaze_center;
    float aspect = params.SourceSize.x / params.SourceSize.y;
    offset.x *= aspect;
    float distance = length(offset);
    offset.x /= aspect; // Restore for later use
    
    // Calculate eccentricity factor (0 = center, 1 = periphery)
    float eccentricity;
    if(distance < params.FoveaRadius)
    {
        // Foveal region - full detail with sharpening
        eccentricity = 0.0;
    }
    else if(distance < params.TransitionRadius)
    {
        // Transition zone - smooth falloff
        float t = (distance - params.FoveaRadius) / (params.TransitionRadius - params.FoveaRadius);
        eccentricity = smoothstep(0.0, 1.0, t);
    }
    else
    {
        // Peripheral region - reduced detail
        eccentricity = 1.0;
    }
    
    // Calculate blur amount based on eccentricity
    float blur_amount = eccentricity * params.PeripheralBlur;
    
    // Sample with appropriate blur
    vec3 color = sampleBlur(vTexCoord, blur_amount);
    
    // Apply sharpening in foveal region
    if(eccentricity < 0.5 && params.Sharpness > 1.0)
    {
        float sharpen_amount = 1.0 - eccentricity * 2.0; // Fade out sharpening
        vec3 sharpened = sharpen(color, vTexCoord);
        color = mix(color, sharpened, sharpen_amount);
    }
    
    // Optional: Add subtle vignette for peripheral darkening (mimics natural vision)
    // Uncomment if desired:
    // float vignette = 1.0 - eccentricity * 0.2;
    // color *= vignette;
    
    FragColor = vec4(color, 1.0);
}
