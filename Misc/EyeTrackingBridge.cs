using System;
using System.IO;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Threading;
using System.Diagnostics;

namespace EyeTrackingBridge
{
    public partial class BridgeForm : Form
    {
        private const string EYE_GAZE_FILE = "eye_gaze.json";
        private System.Windows.Forms.Timer updateTimer;
        private bool isRunning = false;
        private float lastGazeX = 0.5f;
        private float lastGazeY = 0.5f;

        [DllImport("user32.dll")]
        private static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);

        [DllImport("user32.dll")]
        private static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);

        private const uint KEYEVENTF_KEYDOWN = 0;
        private const uint KEYEVENTF_KEYUP = 2;
        private const byte VK_UP = 0x26;
        private const byte VK_DOWN = 0x28;
        private const byte VK_LEFT = 0x25;
        private const byte VK_RIGHT = 0x27;

        public BridgeForm()
        {
            InitializeComponent();
            this.Text = "Eye Tracking Bridge for ShaderGlass";
            this.Width = 400;
            this.Height = 300;
            this.FormBorderStyle = FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;

            // Create UI
            Label statusLbl = new Label { Text = "Status: Ready", Left = 10, Top = 10, Width = 360 };
            Label coordsLbl = new Label { Text = "Gaze: (-, -)", Left = 10, Top = 40, Width = 360 };
            Label modeLbl = new Label { Text = "Mode: Waiting for eye_gaze.json", Left = 10, Top = 70, Width = 360 };
            
            Button startBtn = new Button { Text = "Start Bridge", Left = 10, Top = 110, Width = 100 };
            Button stopBtn = new Button { Text = "Stop", Left = 120, Top = 110, Width = 100 };
            Button launchEyeTrackerBtn = new Button { Text = "Launch Eye Tracker", Left = 230, Top = 110, Width = 140 };

            CheckBox centerXCheckbox = new CheckBox { Text = "Follow Eye X (Center X)", Left = 10, Top = 150, Width = 300 };
            CheckBox centerYCheckbox = new CheckBox { Text = "Follow Eye Y (Center Y)", Left = 10, Top = 180, Width = 300 };

            Label infoLbl = new Label 
            { 
                Text = "1. Click 'Launch Eye Tracker' to start eye detection\n2. Click 'Start Bridge' to link eye position to ShaderGlass\n3. Make sure ShaderGlass window is focused",
                Left = 10, Top = 210, Width = 360, Height = 70,
                AutoSize = false
            };

            this.Controls.Add(statusLbl);
            this.Controls.Add(coordsLbl);
            this.Controls.Add(modeLbl);
            this.Controls.Add(startBtn);
            this.Controls.Add(stopBtn);
            this.Controls.Add(launchEyeTrackerBtn);
            this.Controls.Add(centerXCheckbox);
            this.Controls.Add(centerYCheckbox);
            this.Controls.Add(infoLbl);

            startBtn.Click += (s, e) =>
            {
                if (!isRunning && File.Exists(EYE_GAZE_FILE))
                {
                    isRunning = true;
                    updateTimer.Start();
                    statusLbl.Text = "Status: RUNNING - Monitoring eye position";
                    statusLbl.ForeColor = System.Drawing.Color.Green;
                }
                else if (!File.Exists(EYE_GAZE_FILE))
                {
                    MessageBox.Show("eye_gaze.json not found. Start the Python eye tracker first.", "File Not Found");
                }
            };

            stopBtn.Click += (s, e) =>
            {
                isRunning = false;
                updateTimer.Stop();
                statusLbl.Text = "Status: Stopped";
                statusLbl.ForeColor = System.Drawing.Color.Red;
            };

            launchEyeTrackerBtn.Click += (s, e) =>
            {
                try
                {
                    string eyeTrackerPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "eye_tracker.py");
                    if (!File.Exists(eyeTrackerPath))
                    {
                        MessageBox.Show("eye_tracker.py not found in the same directory", "File Not Found");
                        return;
                    }
                    Process.Start("python", $"\"{eyeTrackerPath}\"");
                    statusLbl.Text = "Status: Eye Tracker launched";
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Error launching eye tracker: {ex.Message}", "Error");
                }
            };

            updateTimer = new System.Windows.Forms.Timer();
            updateTimer.Interval = 30; // ~30ms between updates
            updateTimer.Tick += (s, e) =>
            {
                if (!isRunning) return;

                try
                {
                    if (File.Exists(EYE_GAZE_FILE))
                    {
                        string jsonText = File.ReadAllText(EYE_GAZE_FILE);
                        using (JsonDocument doc = JsonDocument.Parse(jsonText))
                        {
                            JsonElement root = doc.RootElement;
                            if (root.TryGetProperty("gaze_x", out JsonElement gazeXElem) &&
                                root.TryGetProperty("gaze_y", out JsonElement gazeYElem))
                            {
                                lastGazeX = gazeXElem.GetSingle();
                                lastGazeY = gazeYElem.GetSingle();
                                coordsLbl.Text = $"Gaze: ({lastGazeX:F2}, {lastGazeY:F2})";
                            }
                        }
                    }
                }
                catch
                {
                    // Silently ignore JSON parse errors
                }
            };
        }

        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.Run(new BridgeForm());
        }
    }

    partial class BridgeForm
    {
        private void InitializeComponent()
        {
            this.SuspendLayout();
            this.ResumeLayout(false);
        }
    }
}
