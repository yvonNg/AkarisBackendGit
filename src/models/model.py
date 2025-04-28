# Author: Ng Yee Von
# Created date: 21/04/2025
# Last Updated: 24/4/2025
# model.py is to define database structure(tables)

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import func, Enum as SqlEnum
import enum
from src.database import Base  # make sure to use the correct relative path

#-------------User Model------------------

class UserStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    deleted = "deleted"

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, index=True)
    password = Column(String, nullable=False) #stores hashed ps
    phone_number = Column(String(15), nullable=False)
    registered_date = Column(DateTime, default=func.now())
    last_login_date = Column(DateTime)
    user_status = Column(SqlEnum(UserStatus), default=UserStatus.active)
    user_is_active = Column(Boolean, default=True, nullable=False)

    # relationship between tables
    logins2users = relationship("Login", back_populates="user2logins")
    farms2users = relationship("Farm", back_populates="user2farms")
    activity2user = relationship("CropActivity", back_populates="user2Activity", cascade="save-update, merge")

    # for easier logging
    def __repr__(self):
        return f"<User(id={self.user_id}, email={self.email})>"

#-------------Login Model------------------

class Login(Base):
    __tablename__ = "user_logins"

    login_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    login_timestamp = Column(DateTime, default=func.now())
    ip_address = Column(String(45), nullable=False)
    
    # relationship between tables
    user2logins = relationship("User", back_populates="logins2users") #back_populates allows bi-directional relationship
    
    # for easier logging
    def __repr__(self):
        return f"<Login(id={self.login_id}, user_id={self.user_id})>"

#-------------Farm Model------------------

class FarmStatusEnum(enum.Enum):
    active ="active"
    inactive = "inactive"
    terminated = "terminated"

class Farm(Base):
    __tablename__ = "farms"

    farm_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    farm_abbrev = Column(String(50), nullable=False)
    crop_type = Column(String(50), nullable=False)
    farm_size = Column(Numeric(10,2), nullable=False)
    farm_location = Column(String, nullable=False)
    farm_status = Column(SqlEnum(FarmStatusEnum), default=FarmStatusEnum.active)
    farm_is_active = Column(Boolean, nullable=False, default=True)
    record_created_date = Column(DateTime, default=func.now())
    record_updated_date = Column(DateTime, default=None, onupdate=func.now(), nullable=True)

    # relationship between tables
    user2farms = relationship("User", back_populates="farms2users") 
    farmE2farms = relationship("FarmExpect", back_populates="farm2farmE")
    cropDtl2farm = relationship("CropDtl", back_populates="farm2cropDtl")
    ActivityInFarm = relationship("CropActivity", back_populates="farmActivity")
    expensesInFarm = relationship("Expense", back_populates="farm2expenses")
    #payload2farm = relationship("Payload", back_populates="farm2payload")

    # for easier logging
    def __repr__(self):
        return f"<Farm(id={self.farm_id}, crop_type={self.crop_type})>"

#--------------Farm Expectation Model-----------------

class FarmExpectationEnum(enum.Enum):
    active = "active"
    deleted = "deleted"
    updated = "updated"

class FarmExpect(Base):
    __tablename__ = "farm_expect"

    farm_expect_id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.farm_id"), nullable=False, index=True)
    farm_abbrev = Column(String(50), nullable=False)
    expected_harvest_date = Column(Date, nullable=False)
    expected_harvest_base_uom = Column(Numeric(10,2), nullable=False)
    expected_income = Column(Numeric(10,2), nullable=False)
    record_status = Column(SqlEnum(FarmExpectationEnum), default=FarmExpectationEnum.active)
    record_created_date = Column(DateTime, default=func.now())
    record_updated_date = Column(DateTime, default=None, onupdate=func.now(), nullable=True)
    # relationship
    farm2farmE = relationship("Farm", back_populates="farmE2farms")

    # for easier logging
    def __repr__(self):
        return f"<FarmExpect(id={self.farm_expect_id}, farm={self.farm_id})>"
    
#--------------Crop Model-----------------

class CropStatusEnum(enum.Enum):
    active ="active"
    inactive = "inactive"
    terminated = "terminated"

class CropGrowingStageEnum(enum.Enum):
    sproting = "sprouting"
    growing = "growing"
    flowering = "flowering"
    fruiting = "fruiting"
    harvest = "harvest"
    post_harvest = "post-harvest"

class CropDtl(Base):
    __tablename__ = "crops"

    crop_id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.farm_id"), index=True, nullable=False)
    nfc_code = Column(String(30), unique=True, index=True, nullable=False)
    farm_abbrev = Column(String(50), nullable=False)
    crop_type = Column(String(30), nullable=False, index=True)
    crop_subtype = Column(String(50), nullable=True)
    plantation_date = Column(Date, nullable=False)
    method_id = Column(Integer, ForeignKey("plant_method.plant_method_id"), nullable = False, index=True)
    crop_yrs = Column(Integer, nullable=False)
    crop_stage = Column(SqlEnum(CropGrowingStageEnum))
    last_harvest_date = Column(DateTime)
    record_created_date = Column(DateTime, default=func.now(), nullable=False)
    crop_modified_date = Column(DateTime)
    crop_status = Column(SqlEnum(CropStatusEnum), default=CropStatusEnum.active)
    crop_is_active = Column(Boolean, default=True)

    # relationship
    farm2cropDtl = relationship("Farm", back_populates="cropDtl2farm")
    method2CropDtl = relationship("PlantMethod", back_populates="cropDtl2method")
    daily2cropDtl = relationship("CropDaily", back_populates="cropDtl2daily", cascade="save-update, merge")
    activity2cropDtl = relationship("CropActivity", back_populates="cropDtl2activity")
    harvests = relationship("Harvest", back_populates="cropDtl2harvest")

    # for easier logging
    def __repr__(self):
        return f"<CropDtl(id={self.crop_id}, updated_date={self.crop_modified_date})>"
    
#--------------Daily Crop Model----------------

class DailyCropStatusEnum(enum.Enum):
    active = "active"
    deleted = "deleted"
    updated = "updated"

class CropDaily(Base):
    __tablename__ = "crop_daily"

    daily_id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.crop_id"), nullable=False)
    nfc_code = Column(String(30), nullable=False, index=True)
    crop_stage = Column(SqlEnum(CropGrowingStageEnum), nullable=False)
    stage_duration_day = Column(Integer, nullable=True)
    crop_status = Column(SqlEnum(DailyCropStatusEnum), default=DailyCropStatusEnum.active)
    record_created_date = Column(DateTime, default=func.now(), nullable = False, index=True)
    record_updated_date = Column(DateTime, default=None, onupdate=func.now(), nullable=True)

    #relationship
    cropDtl2daily = relationship("CropDtl", back_populates="daily2cropDtl")
    # for easier logging
    def __repr__(self):
        return f"<CropDaily(id={self.daily_id}, crop_id={self.crop_id})>"
    
#--------------Crop Activity Model------------------

class CropActivityEnum(enum.Enum):
    watering = "watering"
    fertilizing = "fertilizing"
    pesticiding = "pesticiding"
    weeding = "weeding"
    transplanting = "transplanting"
    disease = "disease treatment"
    pest = "pest inspection"
    other = "other"
    
class CropActivity(Base):
    __tablename__="crop_activities"

    activity_id = Column(Integer, primary_key=True, unique=True, index=True)
    farm_id = Column(Integer,ForeignKey("farms.farm_id"), nullable=False, index=True)
    crop_id = Column(Integer, ForeignKey("crops.crop_id"), nullable=True, index=True)
    nfc_code = Column(String(30), nullable=True, index=True)
    activity_name = Column(SqlEnum(CropActivityEnum), nullable=False)
    other_activity = Column(String(50), nullable=True)
    activity_details = Column(Text, nullable=True)
    record_created_date = Column(DateTime, default=func.now(), nullable=False)
    record_created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    record_updated_date = Column(DateTime, default=None, onupdate=func.now(), nullable=True)
    record_is_active = Column(Boolean, default=True)

    #relationship
    farmActivity = relationship("Farm", back_populates="ActivityInFarm")
    cropDtl2activity = relationship("CropDtl", back_populates="activity2cropDtl")
    user2Activity = relationship("User", back_populates="activity2user")

    # for easier logging
    def __repr__(self):
        return f"<CropActivity(id={self.activity_id}, activity={self.activity_name})>"

#-------------Crop Planting Method Model---------------

class MethodStatusEnum(enum.Enum):
    active = "active"
    inactive = "inactive"
    deleted = "deleted"

class PlantMethodEnum(enum.Enum):
    transplant = "transplant"
    direct_sowing = "direct sowing"
    cutting = "cutting"
    grafting = "grafting"
    other = "other"

class PlantMethod(Base):
    __tablename__ = "plant_method"

    plant_method_id = Column(Integer, primary_key=True, index=True)
    method = Column(String(50), nullable=False, index=True)
    other_method = Column(String(100), nullable=True)
    record_created_by = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)
    record_status = Column(SqlEnum(MethodStatusEnum), default=MethodStatusEnum.active, nullable=False, index=True)
    record_created_date = Column(DateTime, default=func.now(), nullable=False)
    record_updated_date = Column(DateTime, default=None, onupdate=func.now(), nullable=True)

    # relationship
    cropDtl2method = relationship("CropDtl", back_populates="method2CropDtl")

    def __repr__(self):
        return f"<PlantMethod(id={self.plant_method_id}, method={self.method}, other={self.other_method})>"
    
#--------------Expenses-------------------

class RecordStatusEnum(enum.Enum):
    active = "active"
    deleted = "deleted"

# Expense Model
class Expense(Base):
    __tablename__ = "expenses"

    expenses_id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.farm_id"), nullable=False, index=True)
    category = Column(String(50), nullable=False) 
    description = Column(Text, nullable=True)
    amount = Column(Numeric(10,4), nullable=False) 
    transaction_date = Column(DateTime, nullable=False)
    record_status = Column(SqlEnum(RecordStatusEnum), default=RecordStatusEnum.active, nullable=False)
    record_created_date = Column(DateTime, default=func.now(), nullable=False)
    record_updated_date = Column(DateTime, default=None, onupdate=func.now(), nullable=True)

    # Relationship (if you want to backtrack expenses from farm)
    farm2expenses = relationship("Farm", back_populates="expensesInFarm")

    def __repr__(self):
        return f"<Expense(id={self.expenses_id}, category={self.category}, amount={self.amount})>"
    
#---------------Harvest Model-----------------

class HarvestUnitEnum(enum.Enum):
    kg = "kg"
    unit = "unit"

class HarvestQualityEnum(enum.Enum):
    excellent = "excellent"
    good = "good"
    fair = "fair"
    poor = "poor"

class Harvest(Base):
    __tablename__ = "harvest"

    harvest_id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.crop_id"), nullable=False, index=True)
    nfc_code = Column(String(30), nullable=False, index=True)
    quantity = Column(Numeric(10, 4), nullable=False)
    harvest_unit = Column(SqlEnum(HarvestUnitEnum), nullable=False)
    estimated_kg = Column(Numeric(10, 4), nullable=True)
    harvest_avg_quality = Column(SqlEnum(HarvestQualityEnum), nullable=False)
    earn = Column(Numeric(10, 4), nullable=False)
    harvest_date = Column(DateTime, nullable=False)
    record_status = Column(SqlEnum(RecordStatusEnum), default=RecordStatusEnum.active, nullable=False)
    record_created_date = Column(DateTime, default=func.now(), nullable=False)
    record_updated_date = Column(DateTime, default=None, onupdate=func.now(), nullable=True)

    # Relationship
    cropDtl2harvest = relationship("CropDtl", back_populates="harvests")

    def __repr__(self):
        return f"<Harvest(id={self.harvest_id}, crop_id={self.crop_id}, quantity={self.quantity})>"

