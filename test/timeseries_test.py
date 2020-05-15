from io import StringIO

from libs.datasets.dataset_utils import AggregationLevel
from libs.datasets.sources import cds_dataset
from libs.datasets.timeseries import TimeseriesDataset
from test.dataset_utils_test import to_dict
import pandas as pd
import pytest


# turns all warnings into errors for this module
pytestmark = pytest.mark.filterwarnings("error")


def test_get_subset():
    input_df = pd.read_csv(
        StringIO(
            "city,county,state,fips,country,aggregation_level,date,metric\n"
            "Smithville,,ZZ,97123,USA,city,2020-03-23,march23-removed\n"
            "New York City,,ZZ,97324,USA,city,2020-03-22,march22-nyc\n"
            "New York City,,ZZ,97324,USA,city,2020-03-24,march24-nyc\n"
            ",North County,ZZ,97001,USA,county,2020-03-23,county-not-touched\n"
            ",,ZZ,97001,USA,state,2020-03-23,mystate\n"
            ",,,,UK,country,2020-03-23,foo\n"
        )
    )
    ts = TimeseriesDataset(input_df)

    assert set(ts.get_subset(AggregationLevel.COUNTRY).data['country']) == {'UK'}
    assert set(ts.get_subset(AggregationLevel.STATE).data['metric']) == {'mystate'}
    assert set(ts.get_subset(None, on="2020-03-22").data['metric']) == {'march22-nyc'}
    assert set(ts.get_subset(None, after="2020-03-23").data['metric']) == {'march24-nyc'}
