import React, {
    useEffect,
    useRef,
    useState,
    useCallback,
} from "react";

interface StarsBackgroundProps {
    factor?: number;
    speed?: number;
    starColor?: string;
    pointerEvents?: boolean;
}

export const StarsBackground = ({
    factor = 0.05,
    speed = 40, // Reduced default speed for smoothness
    starColor = "#fff",
    pointerEvents = true,
}: StarsBackgroundProps) => {
    const [size, setSize] = useState({ width: 0, height: 0 });
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const requestRef = useRef<number>();
    const stars = useRef<any[]>([]);
    const cursor = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
    const lastTimeRef = useRef<number>(0);

    const generateStars = useCallback((width: number, height: number) => {
        const area = width * height;
        const amount = Math.floor(area * factor * 0.001);
        const newStars = [];
        for (let i = 0; i < amount; i++) {
            newStars.push({
                x: Math.random() * width,
                y: Math.random() * height,
                z: Math.random() * width, // depth
                size: Math.random(),
            });
        }
        return newStars;
    }, [factor]);

    const update = useCallback((time: number) => {
        if (!canvasRef.current) return;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        if (!lastTimeRef.current) lastTimeRef.current = time;
        const deltaTime = (time - lastTimeRef.current) / 1000;
        lastTimeRef.current = time;

        const width = canvas.width;
        const height = canvas.height;

        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = starColor;

        // Center of screen
        let cx = width / 2;
        let cy = height / 2;

        // Apply pointer influence with easing
        if (pointerEvents) {
            cx += (cursor.current.x - width / 2) * 0.05; // Smoother tracking
            cy += (cursor.current.y - height / 2) * 0.05;
        }

        // Normalized speed based on screen width to align with "pixel" speed roughly
        // adjusted by delta time for framerate independence
        const moveDistance = speed * deltaTime * 5;

        stars.current.forEach((star) => {
            // Move star closer
            star.z -= moveDistance;

            // Reset if passed screen
            if (star.z <= 0) {
                star.z = width;
                star.x = Math.random() * width;
                star.y = Math.random() * height;
            }

            // Project 3D position to 2D
            const k = 128.0 / Math.max(0.1, star.z); // Prevent infinite size/div by zero
            const px = (star.x - width / 2) * k + cx;
            const py = (star.y - height / 2) * k + cy;

            // Draw only if within bounds
            if (px >= 0 && px <= width && py >= 0 && py <= height) {
                // Size scales with proximity, but capped to avoid massive blobs
                const s = Math.min((1 - star.z / width) * 3, 3);

                // Simple opacity fade for distant stars or stars just entering
                const opacity = Math.min(1, (1 - star.z / width));

                ctx.globalAlpha = opacity;
                ctx.beginPath();
                ctx.arc(px, py, s, 0, Math.PI * 2);
                ctx.fill();
                ctx.globalAlpha = 1.0;
            }
        });

        requestRef.current = requestAnimationFrame(update);
    }, [speed, starColor, pointerEvents]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const handleResize = () => {
            if (canvas.parentElement) {
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight;
                setSize({ width: canvas.width, height: canvas.height });
                stars.current = generateStars(canvas.width, canvas.height);
            }
        };

        handleResize();
        window.addEventListener("resize", handleResize);

        // Initial start
        requestRef.current = requestAnimationFrame(update);

        return () => {
            window.removeEventListener("resize", handleResize);
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        };
    }, [generateStars, update]);

    // Handle pointer events
    const handleMouseMove = (e: React.MouseEvent) => {
        if (!pointerEvents) return;
        const rect = canvasRef.current?.getBoundingClientRect();
        if (rect) {
            cursor.current = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top,
            };
        }
    };

    return (
        <div
            className="absolute inset-0 w-full h-full"
            onMouseMove={handleMouseMove}
        >
            <canvas
                ref={canvasRef}
                className="absolute inset-0 w-full h-full block"
                style={{ pointerEvents: 'none' }}
            />
        </div>
    );
};
