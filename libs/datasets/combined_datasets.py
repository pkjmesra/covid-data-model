from typing import Dict, Type, List, NewType
import functools
import pandas as pd
from libs.datasets import dataset_utils
from libs.datasets import dataset_base
from libs.datasets import data_source
from libs.datasets.timeseries import TimeseriesDataset
from libs.datasets.latest_values_dataset import LatestValuesDataset
from libs.datasets.sources.state_interventions import StateInterventions
from libs.datasets.sources.jhu_dataset import JHUDataset
from libs.datasets.sources.nha_hospitalization import NevadaHospitalAssociationData
from libs.datasets.sources.cds_dataset import CDSDataset
from libs.datasets.sources.covid_tracking_source import CovidTrackingDataSource
from libs.datasets.sources.covid_care_map import CovidCareMapBeds
from libs.datasets.sources.fips_population import FIPSPopulation
from libs.datasets import CommonFields
from libs.datasets import dataset_filter
from libs import us_state_abbrev

FeatureDataSourceMap = NewType(
    'FeatureDataSourceMap', Dict[str, List[Type[data_source.DataSource]]]
)

# Below are two instances of feature definitions. These define
# how to assemble values for a specific field.  Right now, we only
# support overlaying values. i.e. a row of
# {CommonFields.POSITIVE_TESTS: [CDSDataset, CovidTrackingDataSource]}
# will first get all values for positive tests in CDSDataset and then overlay any data
# From CovidTracking.
# This is just a start to this sort of definition - in the future, we may want more advanced
# capabilities around what data to apply and how to apply it.
ALL_FIELDS_FEATURE_DEFINITION: FeatureDataSourceMap = {
    CommonFields.CASES: [JHUDataset],
    CommonFields.DEATHS: [JHUDataset],
    CommonFields.RECOVERED: [JHUDataset],
    CommonFields.CUMULATIVE_ICU: [CovidTrackingDataSource],
    CommonFields.CUMULATIVE_HOSPITALIZED: [CovidTrackingDataSource],
    CommonFields.CURRENT_ICU: [
        CovidTrackingDataSource, NevadaHospitalAssociationData
    ],
    CommonFields.CURRENT_HOSPITALIZED: [
        CovidTrackingDataSource, NevadaHospitalAssociationData
    ],
    CommonFields.CURRENT_VENTILATED: [
        CovidTrackingDataSource, NevadaHospitalAssociationData
    ],
    CommonFields.INTERVENTION: [StateInterventions],
    CommonFields.POPULATION: [FIPSPopulation],
    CommonFields.STAFFED_BEDS: [CovidCareMapBeds],
    CommonFields.LICENSED_BEDS: [CovidCareMapBeds],
    CommonFields.ICU_BEDS: [CovidCareMapBeds, NevadaHospitalAssociationData],
    CommonFields.ALL_BED_TYPICAL_OCCUPANCY_RATE: [CovidCareMapBeds],
    CommonFields.ICU_TYPICAL_OCCUPANCY_RATE: [CovidCareMapBeds],
    CommonFields.MAX_BED_COUNT: [CovidCareMapBeds],
    CommonFields.POSITIVE_TESTS: [CDSDataset, CovidTrackingDataSource],
    CommonFields.NEGATIVE_TESTS: [CDSDataset, CovidTrackingDataSource],
}

ALL_TIMESERIES_FEATURE_DEFINITION: FeatureDataSourceMap = {
    CommonFields.CASES: [JHUDataset],
    CommonFields.DEATHS: [JHUDataset],
    CommonFields.RECOVERED: [JHUDataset],
    CommonFields.CUMULATIVE_ICU: [CovidTrackingDataSource],
    CommonFields.CUMULATIVE_HOSPITALIZED: [CovidTrackingDataSource],
    CommonFields.CURRENT_ICU: [
        CovidTrackingDataSource, NevadaHospitalAssociationData
    ],
    CommonFields.CURRENT_HOSPITALIZED: [
        CovidTrackingDataSource, NevadaHospitalAssociationData
    ],
    CommonFields.CURRENT_VENTILATED: [
        CovidTrackingDataSource, NevadaHospitalAssociationData
    ],
    CommonFields.STAFFED_BEDS: [],
    CommonFields.LICENSED_BEDS: [],
    CommonFields.MAX_BED_COUNT: [],
    CommonFields.ICU_BEDS: [NevadaHospitalAssociationData],
    CommonFields.ALL_BED_TYPICAL_OCCUPANCY_RATE: [],
    CommonFields.ICU_TYPICAL_OCCUPANCY_RATE: [],
    CommonFields.POSITIVE_TESTS: [CDSDataset, CovidTrackingDataSource],
    CommonFields.NEGATIVE_TESTS: [CDSDataset, CovidTrackingDataSource],
}

US_STATES_FILTER = dataset_filter.DatasetFilter(
    country="USA", states=list(us_state_abbrev.abbrev_us_state.keys())
)


@functools.lru_cache(None)
def build_timeseries_with_all_fields(filters=None) -> TimeseriesDataset:
    return build_combined_dataset_from_sources(
        TimeseriesDataset,
        ALL_TIMESERIES_FEATURE_DEFINITION,
        filters=filters
    )


@functools.lru_cache(None)
def build_us_timeseries_with_all_fields() -> TimeseriesDataset:
    return build_combined_dataset_from_sources(
        TimeseriesDataset,
        ALL_TIMESERIES_FEATURE_DEFINITION,
        filters=[US_STATES_FILTER]
    )


@functools.lru_cache(None)
def build_us_latest_with_all_fields() -> LatestValuesDataset:
    return build_combined_dataset_from_sources(
        LatestValuesDataset,
        ALL_FIELDS_FEATURE_DEFINITION,
        filters=[US_STATES_FILTER]
    )


@functools.lru_cache(None)
def build_latest_with_all_fields(filters=None) -> LatestValuesDataset:
    return build_combined_dataset_from_sources(
        LatestValuesDataset,
        ALL_FIELDS_FEATURE_DEFINITION,
        filters=filters
    )


def load_data_sources(
    feature_definition_config
) -> Dict[Type[data_source.DataSource], data_source.DataSource]:

    data_source_classes = []
    for classes in feature_definition_config.values():
        data_source_classes.extend(classes)
    loaded_data_sources = {}

    for data_source_class in data_source_classes:
        for data_source_cls in data_source_classes:
            # only load data source once
            if data_source_cls not in loaded_data_sources:
                loaded_data_sources[data_source_cls] = data_source_cls.local()

    return loaded_data_sources


def build_combined_dataset_from_sources(
    target_dataset_cls: Type[dataset_base.DatasetBase],
    feature_definition_config: FeatureDataSourceMap,
    filters: List[dataset_filter.DatasetFilter] = None
):
    """Builds a combined dataset from a feature definition.

    Args:
        target_dataset_cls: Target dataset class.
        feature_definition_config: Dictionary mapping an output field to the
            data sources that will be used to pull values from.
        filters: A list of dataset filters applied to the datasets before
            assembling features.
    """
    loaded_data_sources = load_data_sources(feature_definition_config)

    # Convert data sources to instances of `target_data_cls`.
    intermediate_datasets = {
        data_source_cls: target_dataset_cls.build_from_data_source(source)
        for data_source_cls, source in loaded_data_sources.items()
    }

    # Apply filters to datasets.
    for key in intermediate_datasets:
        dataset = intermediate_datasets[key]
        for data_filter in filters or []:
            dataset = data_filter.apply(dataset)
        intermediate_datasets[key] = dataset

    # Build feature columns from feature_definition_config.
    data = pd.DataFrame({})
    for field, data_source_classes in feature_definition_config.items():
        for data_source_cls in data_source_classes:
            dataset = intermediate_datasets[data_source_cls]

            data = dataset_utils.fill_fields_with_data_source(
                data,
                dataset.data,
                target_dataset_cls.INDEX_FIELDS,
                [field]
            )

    return target_dataset_cls(data)