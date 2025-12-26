@echo off
echo ========================================
echo FHRI Evaluation Script
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate

echo Running BASELINE evaluation (entropy-only)...
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/eval_baseline.json --mode baseline

echo.
echo ========================================
echo.

echo Running FHRI evaluation (full scoring)...
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/eval_fhri.json --mode fhri

echo.
echo ========================================
echo Evaluation complete!
echo Check results/eval_baseline.json and results/eval_fhri.json
echo ========================================
pause






























