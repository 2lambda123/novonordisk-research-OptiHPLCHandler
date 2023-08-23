import unittest
from unittest.mock import MagicMock, patch

from OptiHPLCHandler import EmpowerHandler


class TestEmpowerHandler(unittest.TestCase):
    @patch("OptiHPLCHandler.empower_handler.EmpowerConnection")
    def setUp(self, mock_connection) -> None:
        mock_response = MagicMock()
        mock_response.address = "http://test_address/"
        mock_response.username = "test_username"
        mock_response.project = "test_project"
        mock_connection.return_value = mock_response

        self.handler = EmpowerHandler(
            project="test_project",
            address="http://test_address/",
            username="test_username",
        )

    def test_empower_handler_initialisation(self):
        assert self.handler.project == "test_project"
        assert self.handler.username == "test_username"
        assert self.handler.address == "http://test_address/"

    def test_empower_handler_status(self):
        with self.assertRaises(NotImplementedError):
            self.handler.Status()

    def test_empower_handler_post_sample_list(self):

        sample_list = [
            {
                "Method": "test_method_1",
                "SamplePos": "test_sample_pos_1",
                "SampleName": "test_sample_name_1",
                "InjectionVolume": 1,
            },
            {
                "Method": "test_method_2",
                "SamplePos": "test_sample_pos_2",
                "SampleName": "test_sample_name_2",
                "InjectionVolume": 2,
                "test_field_1": "test_value",
                "test_field_2": 2.3,
            },
        ]
        self.handler.PostExperiment(
            sample_set_method_name="test_sampleset_name",
            sample_list=sample_list,
            plates={},
            audit_trail_message="test_audit_trail_message",
        )
        assert "test_sampleset_name" == self.handler.connection.post.call_args[1]["body"]["name"]
        # Testing that the name is correct in the request
        assert (
            "?auditTrailComment=test_audit_trail_message"
            in self.handler.connection.post.call_args[1]["endpoint"]
        )
        # Testing that the audit trail message is correct
        sample_set_lines = self.handler.connection.post.call_args[1]["body"]["sampleSetLines"]
        first_line_fields = {
            field["name"]: field["value"] for field in sample_set_lines[0]["fields"]
        }
        # Converting the fields in the first sample set line to a dictionary for easier
        # testing
        assert first_line_fields["MethodSetOrReportMethod"] == "test_method_1"
        assert first_line_fields["Vial"] == "test_sample_pos_1"
        assert first_line_fields["SampleName"] == "test_sample_name_1"
        assert first_line_fields["InjVol"] == 1
        second_line_fields = {
            field["name"]: field["value"] for field in sample_set_lines[1]["fields"]
        }
        # Converting the fields in the second sample set line to a dictionary for easier
        # testing
        assert second_line_fields["MethodSetOrReportMethod"] == "test_method_2"
        assert second_line_fields["Vial"] == "test_sample_pos_2"
        assert second_line_fields["SampleName"] == "test_sample_name_2"
        assert second_line_fields["InjVol"] == 2
        assert second_line_fields["test_field_1"] == "test_value"
        assert second_line_fields["test_field_2"] == 2.3
        int_type_list = [
            field["dataType"]
            for field in sample_set_lines[0]["fields"]
            if isinstance(field["value"], int)
        ]
        assert all(
            [int_type == "Double" for int_type in int_type_list]
        )  # Testing that all integer values are doubles
        float_type_list = [
            field["dataType"]
            for field in sample_set_lines[0]["fields"]
            if isinstance(field["value"], float)
        ]
        assert all([float_type == "Double" for float_type in float_type_list])
        # Testing that all float values are doubles
        string_type_list = [
            field["dataType"]
            for field in sample_set_lines[0]["fields"]
            if isinstance(field["value"], str)
        ]
        assert all([string_type == "String" for string_type in string_type_list])
        # Testing that all string values are strings
        dict_type_list = [
            field["dataType"]
            for field in sample_set_lines[0]["fields"]
            if isinstance(field["value"], dict)
        ]
        assert all([dict_type == "Enumerator" for dict_type in dict_type_list])
        # Testing that all dictionary values are strings

    def test_empower_handler_post_sample_list_with_empower_names(self):
        sample_list = [
            {
                "MethodSetOrReportMethod": "test_method_1",
                "Vial": "test_sample_pos_1",
                "InjVol": 1,
                "SampleName": "test_sample_name_1",
            },
        ]
        self.handler.PostExperiment(
            sample_set_method_name="test_sampleset_name",
            sample_list=sample_list,
            plates={},
            audit_trail_message="test_audit_trail_message",
        )
        sample_set_lines = self.handler.connection.post.call_args[1]["body"]["sampleSetLines"]
        sample_fields = {
            field["name"]: field["value"] for field in sample_set_lines[0]["fields"]
        }
        assert sample_fields["MethodSetOrReportMethod"] == "test_method_1"
        assert sample_fields["Vial"] == "test_sample_pos_1"
        assert sample_fields["InjVol"] == 1

    def test_empower_handler_post_sample_list_plates(self):
        plates = {"1": "test_plate_name_1", "2": "test_plate_name_2"}
        self.handler.PostExperiment(
            sample_set_method_name="test_sampleset_name",
            sample_list=[],
            plates=plates,
            audit_trail_message="test_audit_trail_message",
        )
        plate_definition_list = [
            {"plateTypeName": plate_name, "plateLayoutPosition": plate_pos}
            for (plate_pos, plate_name) in plates.items()
        ]
        for plate_definiton in plate_definition_list:
            assert plate_definiton in self.handler.connection.post.call_args[1]["body"]["plates"]

    def test_empower_handler_add_method(self):
        with self.assertRaises(NotImplementedError):
            self.handler.AddMethod(
                template_method="test_template_method",
                new_method="test_new_method",
                changes={},
                audit_trail_message="test_audit_trail_message",
            )

    def test_empower_handler_get_method_list(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "fields": [
                        {"name": "Name", "value": "test_method_name_1"},
                        {"name": "irrelevant_field", "value": "irrelevant_value"},
                    ]
                },
                {
                    "fields": [
                        {"name": "Name", "value": "test_method_name_2"},
                        {"name": "irrelevant_field", "value": "irrelevant_value"},
                    ]
                },
            ]
        }
        self.handler.connection.get.return_value = mock_response

        method_list = self.handler.GetMethodList()
        assert method_list == ["test_method_name_1", "test_method_name_2"]
        assert (
            "methodTypes=MethodSetMethod" in self.handler.connection.get.call_args[1]["endpoint"]
        )  # Check that the correct parameters are passed to the request

    def test_empower_handler_method_with_no_name(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "fields": [
                        {"name": "Name", "value": "test_method_name_1"},
                        {"name": "irrelevant_field", "value": "irrelevant_value"},
                    ]
                },
                {
                    "fields": [
                        {"name": "no_Name", "value": "test_method_name_2"},
                        {"name": "irrelevant_field", "value": "irrelevant_value"},
                    ]  # No fields with name "Name" should give an error
                },
            ]
        }

        self.handler.connection.get.return_value = mock_response
        with self.assertRaises(ValueError):
            self.handler.GetMethodList()

    def test_empower_handler_method_with_two_names(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "fields": [
                        {"name": "Name", "value": "test_method_name_1"},
                        {"name": "Name", "value": "irrelevant_value"},
                    ]  # Two fields with name "Name" should give an error
                },
                {
                    "fields": [
                        {"name": "Name", "value": "test_method_name_2"},
                        {"name": "irrelevant_field", "value": "irrelevant_value"},
                    ]
                },
            ]
        }
        self.handler.connection.get.return_value = mock_response
        with self.assertRaises(ValueError):
            self.handler.GetMethodList()

    def test_empower_handler_get_setup(self):
        with self.assertRaises(NotImplementedError):
            self.handler.GetSetup()

    def test_empower_run_experiment(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        self.handler.connection.post.return_value = mock_response
        self.handler.RunExperiment(
            sample_set_method="test_sample_set_method",
            node="test_node",
            hplc="test_hplc",
        )
        assert (
            self.handler.connection.post.call_args[1]["endpoint"]
            == "acquisition/run-sample-set-method"
        )  # Check that the correct URl is used.
        assert (
            self.handler.connection.post.call_args[1]["body"]["sampleSetMethodName"]
        ) == "test_sample_set_method"
        # Check that the correct sample set method is used.
        assert (
            self.handler.connection.post.call_args[1]["body"]["nodeName"]
        ) == "test_node"  # Check that the correct node is used.
        assert (
            self.handler.connection.post.call_args[1]["body"]["systemName"]
        ) == "test_hplc"  # Check that the correct HPLC is used.
        assert (
            self.handler.connection.post.call_args[1]["body"]["sampleSetName"]
        ) is None  # Check that no sample set name is given
        self.handler.RunExperiment(
            sample_set_method="test_sample_set_method",
            node="test_node",
            hplc="test_hplc",
            sample_set_name="test_sample_set_name",
        )
        assert (
            self.handler.connection.post.call_args[1]["body"]["sampleSetName"]
        ) == "test_sample_set_name"  # Check that the correct sample set name is given

    def test_get_plate_type_names(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                "test_plate_type_name_1",
                "test_plate_type_name_2",
            ]
        }
        self.handler.connection.get.return_value = mock_response
        plate_type_names = self.handler.GetPlateTypeNames()
        assert plate_type_names == [
            "test_plate_type_name_1",
            "test_plate_type_name_2",
        ]

    def test_get_plate_type_names_filter(self):
        self.handler.GetPlateTypeNames(filter_string="test_filter_text")
        assert "?stringFilter=test_filter_text" in self.handler.connection.get.call_args[1]["endpoint"]

    def test_get_node_name_list(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": ["test_node_name_1"]}
        self.handler.connection.get.return_value = mock_response
        node_name_list = self.handler.GetNodeNames()
        assert node_name_list == ["test_node_name_1"]
        assert "acquisition/nodes" in self.handler.connection.get.call_args[1]["endpoint"]

    def test_get_system_name_list(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": ["test_system_name_1"]}
        self.handler.connection.get.return_value = mock_response
        system_name_list = self.handler.GetSystemNames("test_node_name")
        assert system_name_list == ["test_system_name_1"]
        assert (
            "acquisition/chromatographic-systems?nodeName=test_node_name"
            == self.handler.connection.get.call_args[1]["endpoint"]
        )

    def test_get_sample_set_method_list(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": ["test_samplesetmethod_1"]}
        self.handler.connection.get.return_value = mock_response
        samplesetmethod_list = self.handler.GetSampleSetMethods()
        assert samplesetmethod_list == ["test_samplesetmethod_1"]
        assert (
            "project/methods/sample-set-method-list"
            == self.handler.connection.get.call_args[1]["endpoint"]
        )
