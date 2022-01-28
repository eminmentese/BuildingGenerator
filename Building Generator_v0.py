"""
Model exported as python.
Name : Building Generator_v0
Group : RWG
With QGIS : 31616
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsExpression
import processing


class BuildingGenerator_v0(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('InputPolygon', 'Input Polygon', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('NumberofPopulationEstimated', 'Number of Total Population Estimated', type=QgsProcessingParameterNumber.Integer, minValue=1, maxValue=1e+08, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('AverageDwellingArea', 'Average Dwelling Area', type=QgsProcessingParameterNumber.Double, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('AverageFootprintofaBuilding', 'Average Footprint of a Building', type=QgsProcessingParameterNumber.Double, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('AverageStoreyNumber', 'Average Storey Number', type=QgsProcessingParameterNumber.Double, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('Averagepopulationperdwellinghouseholdsiz', 'Average population per dwelling (household size)', type=QgsProcessingParameterNumber.Double, minValue=-1.79769e+308, maxValue=1.79769e+308, defaultValue=None))
        # Net dwelling area per 100 sqm construction area (54/80 in Kathmandu case)
        self.addParameter(QgsProcessingParameterNumber('ReductionFactor', 'Reduction Factor', type=QgsProcessingParameterNumber.Double, minValue=-1.79769e+308, maxValue=1.79769e+308, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Bld_test', 'bld_test', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterBoolean('VERBOSE_LOG', 'Verbose logging', optional=True, defaultValue=False))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(9, model_feedback)
        results = {}
        outputs = {}

        # Random points inside polygons
        alg_params = {
            'INPUT': parameters['InputPolygon'],
            'MIN_DISTANCE': 10,
            'STRATEGY': 0,
            'VALUE': QgsExpression(' @NumberofPopulationEstimated /(((( @AverageFootprintofaBuilding * @AverageStoreyNumber )/ @AverageDwellingArea )* @ReductionFactor )* @Averagepopulationperdwellinghouseholdsiz )').evaluate(),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RandomPointsInsidePolygons'] = processing.run('qgis:randompointsinsidepolygons', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Average Footprint of a Building
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Avg_Footprint',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': parameters['AverageFootprintofaBuilding'],
            'INPUT': outputs['RandomPointsInsidePolygons']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AverageFootprintOfABuilding'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Average Storey Number of a Building
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Avg_Storey_Nr',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': parameters['AverageStoreyNumber'],
            'INPUT': outputs['AverageFootprintOfABuilding']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AverageStoreyNumberOfABuilding'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Average Dwelling Area
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Avg_Dwelling_Area',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': parameters['AverageDwellingArea'],
            'INPUT': outputs['AverageStoreyNumberOfABuilding']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AverageDwellingArea'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Average population per dwelling (household size)
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Avg_Pop_Dwelling',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': parameters['Averagepopulationperdwellinghouseholdsiz'],
            'INPUT': outputs['AverageDwellingArea']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AveragePopulationPerDwellingHouseholdSize'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Total Building Population
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Bld_Population',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': QgsExpression(' ((@AverageFootprintofaBuilding  *  @AverageStoreyNumber ) /  @AverageDwellingArea ) *   @ReductionFactor  *   @Averagepopulationperdwellinghouseholdsiz ').evaluate(),
            'INPUT': outputs['AveragePopulationPerDwellingHouseholdSize']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['TotalBuildingPopulation'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Width calculator
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Width',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': QgsExpression('sqrt(@AverageFootprintofaBuilding)').evaluate(),
            'INPUT': outputs['TotalBuildingPopulation']['OUTPUT'],
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['WidthCalculator'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Length calculator
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Length',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': QgsExpression(' sqrt(@AverageFootprintofaBuilding)').evaluate(),
            'INPUT': outputs['WidthCalculator']['OUTPUT'],
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LengthCalculator'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Rectangles, ovals, diamonds
        alg_params = {
            'HEIGHT': QgsExpression(' sqrt ( @AverageFootprintofaBuilding )').evaluate(),
            'INPUT': outputs['LengthCalculator']['OUTPUT'],
            'ROTATION': QgsExpression('rand(0,360)').evaluate(),
            'SEGMENTS': 5,
            'SHAPE': 0,
            'WIDTH': QgsExpression(' sqrt ( @AverageFootprintofaBuilding )').evaluate(),
            'OUTPUT': parameters['Bld_test']
        }
        outputs['RectanglesOvalsDiamonds'] = processing.run('native:rectanglesovalsdiamonds', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Bld_test'] = outputs['RectanglesOvalsDiamonds']['OUTPUT']
        return results

    def name(self):
        return 'Building Generator_v0'

    def displayName(self):
        return 'Building Generator_v0'

    def group(self):
        return 'RWG'

    def groupId(self):
        return 'RWG'

    def createInstance(self):
        return BuildingGenerator_v0()
