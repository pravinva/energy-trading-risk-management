"""
MLflow Integration for Strategy Tracking
Track strategy parameters, backtests, and live performance
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import json

try:
    import mlflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    print("Warning: MLflow not available")

from app.backend.strategies.base_strategy import BaseStrategy, StrategyParameters
from app.backend.strategies.backtesting import BacktestMetrics


class MLflowTracker:
    """
    MLflow integration for strategy tracking

    Features:
    - Log strategy parameters
    - Track backtest metrics
    - Version strategies
    - Compare performance
    - Model registry integration
    """

    def __init__(
        self,
        experiment_name: str = 'energy-trading-strategies',
        tracking_uri: Optional[str] = None,
    ):
        """
        Initialize MLflow tracker

        Args:
            experiment_name: MLflow experiment name
            tracking_uri: Optional tracking URI (uses Databricks by default)
        """
        if not MLFLOW_AVAILABLE:
            print("MLflow not available - tracking disabled")
            self.enabled = False
            return

        self.enabled = True
        self.experiment_name = experiment_name

        # Set tracking URI (Databricks workspace by default)
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)

        # Set or create experiment
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment:
                mlflow.set_experiment(experiment_name)
            else:
                mlflow.create_experiment(experiment_name)
                mlflow.set_experiment(experiment_name)

            print(f"MLflow experiment: {experiment_name}")

        except Exception as e:
            print(f"Failed to initialize MLflow: {e}")
            self.enabled = False

    def log_backtest(
        self,
        strategy: BaseStrategy,
        metrics: BacktestMetrics,
        run_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Log backtest run to MLflow

        Args:
            strategy: Strategy that was backtested
            metrics: Backtest performance metrics
            run_name: Optional run name

        Returns:
            MLflow run ID or None
        """
        if not self.enabled:
            return None

        try:
            with mlflow.start_run(run_name=run_name or strategy.strategy_name) as run:
                # Log strategy parameters
                self._log_parameters(strategy)

                # Log backtest metrics
                self._log_metrics(metrics)

                # Log artifacts
                self._log_strategy_config(strategy)

                # Add tags
                mlflow.set_tags({
                    'strategy_type': strategy.strategy_type,
                    'strategy_id': strategy.strategy_id,
                    'region_id': strategy.parameters.region_id,
                    'mode': 'backtest',
                })

                print(f"Logged backtest to MLflow: {run.info.run_id}")
                return run.info.run_id

        except Exception as e:
            print(f"Failed to log backtest to MLflow: {e}")
            return None

    def log_live_performance(
        self,
        strategy: BaseStrategy,
        performance_metrics: Dict[str, float],
        step: int,
    ):
        """
        Log live trading performance metrics

        Args:
            strategy: Strategy being executed
            performance_metrics: Current performance metrics
            step: Execution step/iteration
        """
        if not self.enabled:
            return

        try:
            # Log metrics at current step
            for metric_name, value in performance_metrics.items():
                mlflow.log_metric(metric_name, value, step=step)

        except Exception as e:
            print(f"Failed to log live performance: {e}")

    def _log_parameters(self, strategy: BaseStrategy):
        """Log strategy parameters"""
        params = strategy.parameters.model_dump()

        # Log each parameter
        for key, value in params.items():
            if isinstance(value, (int, float, str, bool)):
                mlflow.log_param(key, value)

        # Log strategy-specific parameters
        mlflow.log_param('strategy_type', strategy.strategy_type)
        mlflow.log_param('strategy_name', strategy.strategy_name)

    def _log_metrics(self, metrics: BacktestMetrics):
        """Log backtest metrics"""
        metrics_dict = metrics.model_dump()

        for key, value in metrics_dict.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(key, value)

    def _log_strategy_config(self, strategy: BaseStrategy):
        """Log strategy configuration as artifact"""
        config = {
            'strategy_id': strategy.strategy_id,
            'strategy_name': strategy.strategy_name,
            'strategy_type': strategy.strategy_type,
            'description': strategy.description,
            'parameters': strategy.parameters.model_dump(),
        }

        # Save config as JSON
        with mlflow.start_run():
            mlflow.log_dict(config, 'strategy_config.json')

    def compare_strategies(
        self,
        metric_name: str = 'sharpe_ratio',
        n_best: int = 5,
    ) -> list[Dict[str, Any]]:
        """
        Compare strategies by metric

        Args:
            metric_name: Metric to compare
            n_best: Number of best strategies to return

        Returns:
            List of best strategies with metrics
        """
        if not self.enabled:
            return []

        try:
            client = MlflowClient()
            experiment = mlflow.get_experiment_by_name(self.experiment_name)

            if not experiment:
                return []

            # Get all runs
            runs = client.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=[f'metrics.{metric_name} DESC'],
                max_results=n_best,
            )

            results = []
            for run in runs:
                results.append({
                    'run_id': run.info.run_id,
                    'strategy_name': run.data.tags.get('mlflow.runName', 'Unknown'),
                    'strategy_type': run.data.tags.get('strategy_type', 'Unknown'),
                    metric_name: run.data.metrics.get(metric_name, 0.0),
                    'total_trades': run.data.metrics.get('total_trades', 0),
                    'win_rate': run.data.metrics.get('win_rate', 0.0),
                })

            return results

        except Exception as e:
            print(f"Failed to compare strategies: {e}")
            return []

    def register_model(
        self,
        strategy: BaseStrategy,
        model_name: str,
        run_id: str,
    ) -> Optional[str]:
        """
        Register strategy in MLflow model registry

        Args:
            strategy: Strategy to register
            model_name: Model name in registry
            run_id: MLflow run ID

        Returns:
            Model version or None
        """
        if not self.enabled:
            return None

        try:
            # Register model
            model_uri = f'runs:/{run_id}/model'
            result = mlflow.register_model(model_uri, model_name)

            print(f"Registered model: {model_name} version {result.version}")
            return result.version

        except Exception as e:
            print(f"Failed to register model: {e}")
            return None


# Singleton instance
_tracker: Optional[MLflowTracker] = None


def get_mlflow_tracker() -> MLflowTracker:
    """Get MLflow tracker singleton"""
    global _tracker
    if _tracker is None:
        _tracker = MLflowTracker()
    return _tracker
