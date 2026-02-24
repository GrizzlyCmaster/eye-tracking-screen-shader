// Zoom / fisheye style magnification with eye-tracking support.
// Can use fixed center or dynamic center from eye-tracking.
// Parameter hints: small ZoomStrength and moderate Radius preserve detail.

#version 450

#pragma parameter ZoomStrength "Zoom Strength" 0.3 0.0 0.6 0.01
#pragma parameter ZoomRadius "Zoom Radius" 0.35 0.05 0.9 0.01
#pragma parameter ZoomFalloff "Zoom Falloff" 2.0 0.5 4.0 0.1
#pragma parameter CenterX "Center X (Eye Track)" 0.5 0.0 1.0 0.01
#pragma parameter CenterY "Center Y (Eye Track)" 0.5 0.0 1.0 0.01

layout(push_constant) uniform Push
{
    vec4 SourceSize;
    vec4 OriginalSize;
    vec4 OutputSize;
    uint FrameCount;

    float ZoomStrength;
    float ZoomRadius;
    float ZoomFalloff;
    float CenterX;
    float CenterY;
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

void main()
{
    vec2 center = vec2(params.CenterX, params.CenterY);
    vec2 offset = vTexCoord - center;

    float aspect = params.SourceSize.x / params.SourceSize.y;
    offset.x *= aspect;

    float radius = max(params.ZoomRadius, 0.0001);
    float r = length(offset);

    if(r < radius)
    {
        float t = r / radius;
        float curve = pow(smoothstep(0.0, 1.0, t), params.ZoomFalloff);
        float zoom = mix(1.0 - params.ZoomStrength, 1.0, curve);
        offset *= zoom;
    }

    offset.x /= aspect;
    vec2 sample_uv = clamp(center + offset, vec2(0.0), vec2(1.0));

    FragColor = texture(Source, sample_uv);
}
