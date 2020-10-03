import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, Sequence
from sqlalchemy.orm import scoped_session, sessionmaker

Base = declarative_base()
class Metar(Base):
    __tablename__ = 'metar'
    station_id = Column(String(4), primary_key=True)
    observation_time = Column(DateTime, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    temp_c = Column(Float)
    dewpoint_c = Column(Float)
    wind_dir_degrees = Column(Integer)
    wind_speed_kt = Column(Integer)
    wind_gust_kt = Column(Integer)
    visibility_statute_mi = Column(Float)
    altim_in_hg = Column(Float)
    sea_level_pressure_mb = Column(Float)
    quality_control_flags = Column(Text)
    wx_string = Column(Text)
    sky_cover = Column(String(3))
    cloud_base_ft_agl = Column(Integer)
    flight_category = Column(String(4))
    three_hr_pressure_tendency_mb = Column(Float)
    maxT_c = Column(Float)
    minT_c = Column(Float)
    maxT24hr_c = Column(Float)
    minT24hr_c = Column(Float)
    precip_in = Column(Float)
    pcp3hr_in = Column(Float)
    pcp6hr_in = Column(Float)
    snow_in = Column(Float)
    vert_vis_ft = Column(Integer)
    metar_type = Column(String(5))
    elevation_m = Column(Float)
    raw_text = Column(Text)
    raw_xml = Column(Text)

class Database:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        
    def add_metars(self, metar_data):
        logger = logging.getLogger(__name__)
        session = self.Session()
        for station, data in metar_data.items():
            logger.debug("Adding {} METAR to database".format(station))
            metar = Metar(**data)
            session.merge(metar)

        session.commit()
